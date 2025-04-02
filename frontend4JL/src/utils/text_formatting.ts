import { format } from 'date-fns';

export const formatDate = (dateString: string): string => {
  if (dateString === '-') return '-';
  try {
    return format(new Date(dateString), 'MM/dd/yyyy HH:mm');
  } catch (error) {
    return dateString;
  }
};

export const getStatusColor = (status: string): 'warning' | 'info' | 'success' | 'error' | 'default' => {
  switch (status.toLowerCase()) {
    case 'pending':
      return 'warning';
    case 'running':
      return 'info';
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
}; 