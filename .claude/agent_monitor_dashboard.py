#!/usr/bin/env python3
"""
Agent Monitor Dashboard - Real-time visualization of agent activity
Provides a terminal-based dashboard for monitoring all Claude agents
"""

import os
import sys
import time
import json
import sqlite3
import curses
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import subprocess
import threading
from enum import Enum

class DashboardView(Enum):
    """Available dashboard views"""
    OVERVIEW = "overview"
    AGENTS = "agents"
    TASKS = "tasks"
    MESSAGES = "messages"
    CONFLICTS = "conflicts"
    PERFORMANCE = "performance"
    LOGS = "logs"

class AgentMonitorDashboard:
    """Terminal-based monitoring dashboard for agents"""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path.cwd()
        self.hub_dir = self.base_path / ".claude" / "communication_hub"
        self.db_path = self.hub_dir / "hub.db"
        self.log_dir = self.base_path / ".claude" / "logs"
        
        # Dashboard state
        self.current_view = DashboardView.OVERVIEW
        self.refresh_rate = 2  # seconds
        self.running = True
        self.data_cache = {}
        self.last_update = datetime.now()
        
        # Color pairs for curses
        self.colors = {
            'header': 1,
            'success': 2,
            'warning': 3,
            'error': 4,
            'info': 5,
            'highlight': 6
        }
        
        # Performance tracking
        self.performance_history = defaultdict(lambda: deque(maxlen=50))
        
    def initialize_colors(self):
        """Initialize color pairs for the dashboard"""
        curses.init_pair(self.colors['header'], curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(self.colors['success'], curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(self.colors['warning'], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(self.colors['error'], curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(self.colors['info'], curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(self.colors['highlight'], curses.COLOR_BLACK, curses.COLOR_WHITE)
    
    def fetch_data(self):
        """Fetch latest data from database and system"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Fetch agent status
            cursor.execute('''
                SELECT agent_name, status, current_task, last_heartbeat 
                FROM agent_status 
                ORDER BY agent_name
            ''')
            self.data_cache['agents'] = cursor.fetchall()
            
            # Fetch task statistics
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM tasks 
                GROUP BY status
            ''')
            self.data_cache['task_stats'] = dict(cursor.fetchall())
            
            # Fetch recent tasks
            cursor.execute('''
                SELECT id, title, agent, status, priority, created_at 
                FROM tasks 
                ORDER BY created_at DESC 
                LIMIT 20
            ''')
            self.data_cache['recent_tasks'] = cursor.fetchall()
            
            # Fetch recent messages
            cursor.execute('''
                SELECT type, sender, recipient, priority, timestamp 
                FROM messages 
                ORDER BY timestamp DESC 
                LIMIT 20
            ''')
            self.data_cache['recent_messages'] = cursor.fetchall()
            
            # Fetch conflicts
            cursor.execute('''
                SELECT type, agents, resource, resolution, timestamp 
                FROM conflict_log 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''')
            self.data_cache['conflicts'] = cursor.fetchall()
            
            # Fetch performance metrics
            cursor.execute('''
                SELECT agent, status, COUNT(*) as count,
                       AVG(CASE 
                           WHEN completed_at IS NOT NULL AND created_at IS NOT NULL 
                           THEN julianday(completed_at) - julianday(created_at) 
                           ELSE NULL 
                       END) * 24 * 60 as avg_completion_minutes
                FROM tasks 
                GROUP BY agent, status
            ''')
            
            perf_data = cursor.fetchall()
            self.data_cache['performance'] = defaultdict(dict)
            for agent, status, count, avg_time in perf_data:
                if agent not in self.data_cache['performance']:
                    self.data_cache['performance'][agent] = {
                        'total': 0, 'completed': 0, 'failed': 0, 'avg_time': 0
                    }
                self.data_cache['performance'][agent]['total'] += count
                if status == 'completed':
                    self.data_cache['performance'][agent]['completed'] = count
                    if avg_time:
                        self.data_cache['performance'][agent]['avg_time'] = avg_time
                elif status == 'failed':
                    self.data_cache['performance'][agent]['failed'] = count
            
            conn.close()
            
            # Fetch system status
            self.data_cache['system'] = self.get_system_status()
            
            self.last_update = datetime.now()
            
        except Exception as e:
            self.data_cache['error'] = str(e)
    
    def get_system_status(self) -> Dict:
        """Get system resource usage"""
        status = {}
        
        # Check service health
        services = {
            'backend': 'http://localhost:8000/health/',
            'frontend': 'http://localhost:3000/',
            'identity': 'http://localhost:8001/health'
        }
        
        status['services'] = {}
        for service, url in services.items():
            try:
                result = subprocess.run(
                    ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
                    capture_output=True, text=True, timeout=1
                )
                status['services'][service] = result.stdout == '200'
            except:
                status['services'][service] = False
        
        # Get git status
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True, cwd=self.base_path
            )
            status['git_changes'] = len(result.stdout.splitlines())
        except:
            status['git_changes'] = 0
        
        return status
    
    def draw_header(self, stdscr, title: str):
        """Draw dashboard header"""
        height, width = stdscr.getmaxyx()
        
        # Title bar
        header = f" AGENT MONITOR DASHBOARD - {title} "
        header = header.center(width, '═')
        stdscr.attron(curses.color_pair(self.colors['header']))
        stdscr.addstr(0, 0, header[:width])
        stdscr.attroff(curses.color_pair(self.colors['header']))
        
        # Status line
        status = f"Last Update: {self.last_update.strftime('%H:%M:%S')} | "
        status += f"Refresh: {self.refresh_rate}s | "
        status += f"View: {self.current_view.value}"
        stdscr.addstr(1, 0, status[:width])
        
        # Navigation help
        nav = "Views: [O]verview [A]gents [T]asks [M]essages [C]onflicts [P]erformance [L]ogs | [Q]uit [R]efresh"
        stdscr.addstr(2, 0, nav[:width])
        
        # Separator
        stdscr.addstr(3, 0, '─' * width)
        
        return 4  # Return next line position
    
    def draw_overview(self, stdscr):
        """Draw overview dashboard"""
        y = self.draw_header(stdscr, "OVERVIEW")
        height, width = stdscr.getmaxyx()
        
        # Agent Status Summary
        stdscr.attron(curses.color_pair(self.colors['info']))
        stdscr.addstr(y, 0, "AGENT STATUS")
        stdscr.attroff(curses.color_pair(self.colors['info']))
        y += 1
        
        if 'agents' in self.data_cache:
            for agent_name, status, current_task, last_heartbeat in self.data_cache['agents']:
                if y >= height - 2:
                    break
                    
                # Choose color based on status
                if status == 'available':
                    color = self.colors['success']
                elif status == 'busy':
                    color = self.colors['warning']
                else:
                    color = self.colors['error']
                
                stdscr.attron(curses.color_pair(color))
                status_icon = '●'
                stdscr.addstr(y, 2, status_icon)
                stdscr.attroff(curses.color_pair(color))
                
                agent_info = f" {agent_name:20} {status:12}"
                if current_task:
                    agent_info += f" Working on: {current_task}"
                stdscr.addstr(y, 4, agent_info[:width-4])
                y += 1
        
        y += 1
        
        # Task Statistics
        if y < height - 10:
            stdscr.attron(curses.color_pair(self.colors['info']))
            stdscr.addstr(y, 0, "TASK STATISTICS")
            stdscr.attroff(curses.color_pair(self.colors['info']))
            y += 1
            
            if 'task_stats' in self.data_cache:
                stats = self.data_cache['task_stats']
                total = sum(stats.values())
                
                stdscr.addstr(y, 2, f"Total Tasks: {total}")
                y += 1
                
                for status, count in stats.items():
                    if y >= height - 2:
                        break
                    
                    # Progress bar
                    percentage = (count / total * 100) if total > 0 else 0
                    bar_width = min(30, width - 30)
                    filled = int(bar_width * percentage / 100)
                    bar = '█' * filled + '░' * (bar_width - filled)
                    
                    stdscr.addstr(y, 2, f"{status:12} [{bar}] {count:3} ({percentage:.1f}%)")
                    y += 1
        
        y += 1
        
        # Service Health
        if y < height - 5 and 'system' in self.data_cache:
            stdscr.attron(curses.color_pair(self.colors['info']))
            stdscr.addstr(y, 0, "SERVICE HEALTH")
            stdscr.attroff(curses.color_pair(self.colors['info']))
            y += 1
            
            for service, healthy in self.data_cache['system'].get('services', {}).items():
                if y >= height - 2:
                    break
                    
                color = self.colors['success'] if healthy else self.colors['error']
                status = '✓ Running' if healthy else '✗ Down'
                
                stdscr.attron(curses.color_pair(color))
                stdscr.addstr(y, 2, f"{service:15} {status}")
                stdscr.attroff(curses.color_pair(color))
                y += 1
    
    def draw_agents(self, stdscr):
        """Draw detailed agent view"""
        y = self.draw_header(stdscr, "AGENTS")
        height, width = stdscr.getmaxyx()
        
        if 'agents' not in self.data_cache:
            stdscr.addstr(y, 0, "No agent data available")
            return
        
        # Headers
        headers = f"{'Agent':20} {'Status':12} {'Current Task':30} {'Last Heartbeat':20}"
        stdscr.attron(curses.color_pair(self.colors['highlight']))
        stdscr.addstr(y, 0, headers[:width])
        stdscr.attroff(curses.color_pair(self.colors['highlight']))
        y += 1
        
        for agent_name, status, current_task, last_heartbeat in self.data_cache['agents']:
            if y >= height - 2:
                break
            
            # Choose color based on status
            if status == 'available':
                color = self.colors['success']
            elif status == 'busy':
                color = self.colors['warning']
            else:
                color = self.colors['error']
            
            # Format heartbeat
            if last_heartbeat:
                try:
                    hb_time = datetime.fromisoformat(last_heartbeat)
                    time_diff = datetime.now() - hb_time
                    if time_diff.total_seconds() < 60:
                        hb_str = "Just now"
                    elif time_diff.total_seconds() < 3600:
                        hb_str = f"{int(time_diff.total_seconds() / 60)}m ago"
                    else:
                        hb_str = f"{int(time_diff.total_seconds() / 3600)}h ago"
                except:
                    hb_str = "Unknown"
            else:
                hb_str = "Never"
            
            line = f"{agent_name:20} {status:12} {current_task or 'None':30} {hb_str:20}"
            
            stdscr.attron(curses.color_pair(color))
            stdscr.addstr(y, 0, line[:width])
            stdscr.attroff(curses.color_pair(color))
            y += 1
    
    def draw_tasks(self, stdscr):
        """Draw task queue view"""
        y = self.draw_header(stdscr, "TASKS")
        height, width = stdscr.getmaxyx()
        
        if 'recent_tasks' not in self.data_cache:
            stdscr.addstr(y, 0, "No task data available")
            return
        
        # Headers
        headers = f"{'ID':10} {'Title':30} {'Agent':15} {'Status':12} {'Priority':8}"
        stdscr.attron(curses.color_pair(self.colors['highlight']))
        stdscr.addstr(y, 0, headers[:width])
        stdscr.attroff(curses.color_pair(self.colors['highlight']))
        y += 1
        
        for task_id, title, agent, status, priority, created_at in self.data_cache['recent_tasks']:
            if y >= height - 2:
                break
            
            # Choose color based on priority
            if priority == 1:  # CRITICAL
                color = self.colors['error']
            elif priority == 2:  # HIGH
                color = self.colors['warning']
            else:
                color = 0  # Default
            
            # Truncate title if needed
            title = title[:28] + '..' if len(title) > 30 else title
            
            line = f"{task_id:10} {title:30} {agent:15} {status:12} P{priority}"
            
            if color:
                stdscr.attron(curses.color_pair(color))
            stdscr.addstr(y, 0, line[:width])
            if color:
                stdscr.attroff(curses.color_pair(color))
            y += 1
    
    def draw_messages(self, stdscr):
        """Draw message flow view"""
        y = self.draw_header(stdscr, "MESSAGES")
        height, width = stdscr.getmaxyx()
        
        if 'recent_messages' not in self.data_cache:
            stdscr.addstr(y, 0, "No message data available")
            return
        
        # Headers
        headers = f"{'Type':20} {'From':15} {'To':15} {'Priority':8} {'Time':20}"
        stdscr.attron(curses.color_pair(self.colors['highlight']))
        stdscr.addstr(y, 0, headers[:width])
        stdscr.attroff(curses.color_pair(self.colors['highlight']))
        y += 1
        
        for msg_type, sender, recipient, priority, timestamp in self.data_cache['recent_messages']:
            if y >= height - 2:
                break
            
            # Format timestamp
            try:
                msg_time = datetime.fromisoformat(timestamp)
                time_str = msg_time.strftime('%H:%M:%S')
            except:
                time_str = "Unknown"
            
            line = f"{msg_type:20} {sender:15} {recipient:15} P{priority} {time_str:20}"
            stdscr.addstr(y, 0, line[:width])
            y += 1
    
    def draw_conflicts(self, stdscr):
        """Draw conflict resolution view"""
        y = self.draw_header(stdscr, "CONFLICTS")
        height, width = stdscr.getmaxyx()
        
        if 'conflicts' not in self.data_cache or not self.data_cache['conflicts']:
            stdscr.addstr(y, 0, "No conflicts detected")
            return
        
        for conflict_type, agents, resource, resolution, timestamp in self.data_cache['conflicts']:
            if y >= height - 5:
                break
            
            stdscr.attron(curses.color_pair(self.colors['warning']))
            stdscr.addstr(y, 0, f"Conflict: {conflict_type}")
            stdscr.attroff(curses.color_pair(self.colors['warning']))
            y += 1
            
            stdscr.addstr(y, 2, f"Agents: {agents}")
            y += 1
            stdscr.addstr(y, 2, f"Resource: {resource or 'N/A'}")
            y += 1
            
            try:
                res_data = json.loads(resolution)
                stdscr.addstr(y, 2, f"Resolution: {res_data.get('resolution', 'Unknown')}")
            except:
                stdscr.addstr(y, 2, f"Resolution: {resolution}")
            y += 2
    
    def draw_performance(self, stdscr):
        """Draw performance metrics view"""
        y = self.draw_header(stdscr, "PERFORMANCE")
        height, width = stdscr.getmaxyx()
        
        if 'performance' not in self.data_cache:
            stdscr.addstr(y, 0, "No performance data available")
            return
        
        # Headers
        headers = f"{'Agent':20} {'Total':8} {'Done':8} {'Failed':8} {'Success%':10} {'Avg Time':12}"
        stdscr.attron(curses.color_pair(self.colors['highlight']))
        stdscr.addstr(y, 0, headers[:width])
        stdscr.attroff(curses.color_pair(self.colors['highlight']))
        y += 1
        
        for agent, metrics in self.data_cache['performance'].items():
            if y >= height - 2:
                break
            
            total = metrics.get('total', 0)
            completed = metrics.get('completed', 0)
            failed = metrics.get('failed', 0)
            success_rate = (completed / total * 100) if total > 0 else 0
            avg_time = metrics.get('avg_time', 0)
            
            # Choose color based on success rate
            if success_rate >= 90:
                color = self.colors['success']
            elif success_rate >= 70:
                color = self.colors['warning']
            else:
                color = self.colors['error']
            
            line = f"{agent:20} {total:8} {completed:8} {failed:8} {success_rate:9.1f}% {avg_time:10.1f}m"
            
            stdscr.attron(curses.color_pair(color))
            stdscr.addstr(y, 0, line[:width])
            stdscr.attroff(curses.color_pair(color))
            y += 1
    
    def draw_logs(self, stdscr):
        """Draw recent logs view"""
        y = self.draw_header(stdscr, "LOGS")
        height, width = stdscr.getmaxyx()
        
        log_file = self.log_dir / "coordinator.log"
        if not log_file.exists():
            stdscr.addstr(y, 0, "No log file found")
            return
        
        try:
            # Read last N lines of log file
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-(height-y-2):]
                
                for line in recent_lines:
                    if y >= height - 2:
                        break
                    
                    # Color based on log level
                    if 'ERROR' in line:
                        color = self.colors['error']
                    elif 'WARNING' in line:
                        color = self.colors['warning']
                    elif 'SUCCESS' in line:
                        color = self.colors['success']
                    else:
                        color = 0
                    
                    if color:
                        stdscr.attron(curses.color_pair(color))
                    stdscr.addstr(y, 0, line.strip()[:width])
                    if color:
                        stdscr.attroff(curses.color_pair(color))
                    y += 1
        except Exception as e:
            stdscr.addstr(y, 0, f"Error reading logs: {e}")
    
    def handle_input(self, key):
        """Handle keyboard input"""
        if key == ord('q') or key == ord('Q'):
            self.running = False
        elif key == ord('r') or key == ord('R'):
            self.fetch_data()
        elif key == ord('o') or key == ord('O'):
            self.current_view = DashboardView.OVERVIEW
        elif key == ord('a') or key == ord('A'):
            self.current_view = DashboardView.AGENTS
        elif key == ord('t') or key == ord('T'):
            self.current_view = DashboardView.TASKS
        elif key == ord('m') or key == ord('M'):
            self.current_view = DashboardView.MESSAGES
        elif key == ord('c') or key == ord('C'):
            self.current_view = DashboardView.CONFLICTS
        elif key == ord('p') or key == ord('P'):
            self.current_view = DashboardView.PERFORMANCE
        elif key == ord('l') or key == ord('L'):
            self.current_view = DashboardView.LOGS
        elif key == ord('+'):
            self.refresh_rate = min(10, self.refresh_rate + 1)
        elif key == ord('-'):
            self.refresh_rate = max(1, self.refresh_rate - 1)
    
    def run(self, stdscr):
        """Main dashboard loop"""
        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)  # Non-blocking input
        stdscr.timeout(100)  # Refresh every 100ms
        
        # Initialize colors
        if curses.has_colors():
            curses.start_color()
            self.initialize_colors()
        
        # Initial data fetch
        self.fetch_data()
        
        last_refresh = time.time()
        
        while self.running:
            try:
                # Clear screen
                stdscr.clear()
                
                # Draw current view
                if self.current_view == DashboardView.OVERVIEW:
                    self.draw_overview(stdscr)
                elif self.current_view == DashboardView.AGENTS:
                    self.draw_agents(stdscr)
                elif self.current_view == DashboardView.TASKS:
                    self.draw_tasks(stdscr)
                elif self.current_view == DashboardView.MESSAGES:
                    self.draw_messages(stdscr)
                elif self.current_view == DashboardView.CONFLICTS:
                    self.draw_conflicts(stdscr)
                elif self.current_view == DashboardView.PERFORMANCE:
                    self.draw_performance(stdscr)
                elif self.current_view == DashboardView.LOGS:
                    self.draw_logs(stdscr)
                
                # Refresh display
                stdscr.refresh()
                
                # Handle input
                key = stdscr.getch()
                if key != -1:
                    self.handle_input(key)
                
                # Auto-refresh data
                current_time = time.time()
                if current_time - last_refresh >= self.refresh_rate:
                    self.fetch_data()
                    last_refresh = current_time
                
            except KeyboardInterrupt:
                self.running = False
            except curses.error:
                pass  # Ignore curses errors (usually from terminal resize)
            except Exception as e:
                # Show error in status area
                self.data_cache['error'] = str(e)

def main():
    """Main entry point"""
    dashboard = AgentMonitorDashboard()
    
    try:
        # Check if database exists
        if not dashboard.db_path.exists():
            print("Communication hub database not found.")
            print("Please start the communication hub first:")
            print("  python3 .claude/agent_communication_hub.py start")
            sys.exit(1)
        
        # Run dashboard in curses
        curses.wrapper(dashboard.run)
        
    except KeyboardInterrupt:
        print("\nDashboard terminated by user")
    except Exception as e:
        print(f"Error running dashboard: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()