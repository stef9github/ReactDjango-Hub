/**
 * Communication Service API Client
 * Handles notifications, messages, and real-time communication through Kong Gateway
 */

import { BaseServiceClient, BaseServiceConfig, TokenStorage } from './base';

// Communication Service Types
export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  data?: Record<string, any>;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: 'text' | 'file' | 'image' | 'system';
  created_at: string;
  read_at?: string;
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  name?: string;
  participants: string[];
  last_message?: Message;
  created_at: string;
  updated_at: string;
}

export interface CreateNotificationRequest {
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  recipient_id?: string;
  data?: Record<string, any>;
}

export interface SendMessageRequest {
  conversation_id: string;
  content: string;
  message_type?: 'text' | 'file' | 'image';
  metadata?: Record<string, any>;
}

export interface CreateConversationRequest {
  name?: string;
  participants: string[];
}

// Communication Service Client
export class CommunicationServiceClient extends BaseServiceClient {
  constructor(
    config?: Partial<BaseServiceConfig>,
    tokenStorage?: TokenStorage
  ) {
    const defaultConfig: BaseServiceConfig = {
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    super({ ...defaultConfig, ...config }, tokenStorage);
  }

  // Notification endpoints
  async getNotifications(limit?: number, offset?: number): Promise<Notification[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<Notification[]>('GET', `/api/v1/notifications${query}`);
  }

  async getNotificationById(id: string): Promise<Notification> {
    return this.makeRequest<Notification>('GET', `/api/v1/notifications/${id}`);
  }

  async createNotification(data: CreateNotificationRequest): Promise<Notification> {
    return this.makeRequest<Notification>('POST', '/api/v1/notifications', data);
  }

  async markNotificationAsRead(id: string): Promise<Notification> {
    return this.makeRequest<Notification>('PATCH', `/api/v1/notifications/${id}/read`);
  }

  async markAllNotificationsAsRead(): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('POST', '/api/v1/notifications/mark-all-read');
  }

  async deleteNotification(id: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('DELETE', `/api/v1/notifications/${id}`);
  }

  // Message endpoints
  async getMessages(conversationId: string, limit?: number, offset?: number): Promise<Message[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<Message[]>('GET', `/api/v1/messages/conversation/${conversationId}${query}`);
  }

  async getMessageById(id: string): Promise<Message> {
    return this.makeRequest<Message>('GET', `/api/v1/messages/${id}`);
  }

  async sendMessage(data: SendMessageRequest): Promise<Message> {
    return this.makeRequest<Message>('POST', '/api/v1/messages', data);
  }

  async markMessageAsRead(id: string): Promise<Message> {
    return this.makeRequest<Message>('PATCH', `/api/v1/messages/${id}/read`);
  }

  async deleteMessage(id: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('DELETE', `/api/v1/messages/${id}`);
  }

  // Conversation endpoints
  async getConversations(): Promise<Conversation[]> {
    return this.makeRequest<Conversation[]>('GET', '/api/v1/conversations');
  }

  async getConversationById(id: string): Promise<Conversation> {
    return this.makeRequest<Conversation>('GET', `/api/v1/conversations/${id}`);
  }

  async createConversation(data: CreateConversationRequest): Promise<Conversation> {
    return this.makeRequest<Conversation>('POST', '/api/v1/conversations', data);
  }

  async updateConversation(id: string, data: Partial<CreateConversationRequest>): Promise<Conversation> {
    return this.makeRequest<Conversation>('PATCH', `/api/v1/conversations/${id}`, data);
  }

  async deleteConversation(id: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('DELETE', `/api/v1/conversations/${id}`);
  }

  async addParticipantToConversation(conversationId: string, participantId: string): Promise<Conversation> {
    return this.makeRequest<Conversation>('POST', `/api/v1/conversations/${conversationId}/participants`, {
      participant_id: participantId,
    });
  }

  async removeParticipantFromConversation(conversationId: string, participantId: string): Promise<Conversation> {
    return this.makeRequest<Conversation>('DELETE', `/api/v1/conversations/${conversationId}/participants/${participantId}`);
  }
}

// Default client instance
export const communicationClient = new CommunicationServiceClient();