/**
 * Atoms - Foundational UI Components Barrel Export
 * Basic building blocks for the component library
 */

// Core form components
export {
  Button,
  ButtonGroup,
  IconButton,
  buttonUtils,
} from './Button';

export type {
  ButtonProps,
  ButtonGroupProps,
  IconButtonProps,
} from './Button';

export {
  Input,
  Textarea,
  inputUtils,
} from './Input';

export type {
  InputProps,
  TextareaProps,
} from './Input';

// Layout components
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  CardImage,
  CardActions,
  AuthCard,
  StatsCard,
  cardUtils,
} from './Card';

export type {
  CardProps,
  CardHeaderProps,
  CardTitleProps,
  CardFooterProps,
  CardImageProps,
  CardActionsProps,
  AuthCardProps,
  StatsCardProps,
} from './Card';

// Feedback components
export {
  Alert,
  AlertTitle,
  AlertDescription,
  AlertActions,
  alertUtils,
} from './Alert';

export type {
  AlertProps,
} from './Alert';

export {
  Badge,
  NumberBadge,
  StatusBadge,
  RemovableBadge,
  InteractiveBadge,
  badgeUtils,
} from './Badge';

export type {
  BadgeProps,
  NumberBadgeProps,
  StatusBadgeProps,
  RemovableBadgeProps,
  InteractiveBadgeProps,
} from './Badge';

// Re-export utilities
export { cn, focusRing, disabled, srOnly } from '@/lib/utils/cn';