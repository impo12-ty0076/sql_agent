import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BackupConfigTable from '../BackupConfigTable';
import { BackupConfig } from '../../../types/systemSettings';

const mockBackupConfigs: BackupConfig[] = [
  {
    id: '1',
    name: 'Daily Backup',
    schedule: 'daily',
    retention: 7,
    includeSettings: true,
    includeUserData: true,
    includeQueryHistory: true,
    destination: '/backups/daily',
    lastBackupAt: new Date('2023-01-01T12:00:00'),
    nextBackupAt: new Date('2023-01-02T12:00:00'),
    status: 'active',
  },
  {
    id: '2',
    name: 'Weekly Backup',
    schedule: 'weekly',
    retention: 4,
    includeSettings: true,
    includeUserData: true,
    includeQueryHistory: false,
    destination: '/backups/weekly',
    lastBackupAt: new Date('2022-12-25T12:00:00'),
    nextBackupAt: new Date('2023-01-01T12:00:00'),
    status: 'inactive',
  },
];

const mockProps = {
  backupConfigs: mockBackupConfigs,
  loading: false,
  onEdit: jest.fn(),
  onDelete: jest.fn(),
  onBackupNow: jest.fn(),
};

describe('BackupConfigTable', () => {
  it('renders backup config table with data', () => {
    render(<BackupConfigTable {...mockProps} />);

    // Check if table headers are rendered
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Schedule')).toBeInTheDocument();
    expect(screen.getByText('Retention')).toBeInTheDocument();
    expect(screen.getByText('Included Data')).toBeInTheDocument();

    // Check if backup config data is rendered
    expect(screen.getByText('Daily Backup')).toBeInTheDocument();
    expect(screen.getByText('Daily')).toBeInTheDocument();
    expect(screen.getByText('7 backups')).toBeInTheDocument();
    expect(screen.getByText('Weekly Backup')).toBeInTheDocument();
    expect(screen.getByText('Weekly')).toBeInTheDocument();
    expect(screen.getByText('4 backups')).toBeInTheDocument();

    // Check if included data is displayed correctly
    expect(screen.getByText('Settings, User Data, Query History')).toBeInTheDocument();
    expect(screen.getByText('Settings, User Data')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<BackupConfigTable {...mockProps} loading={true} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<BackupConfigTable {...mockProps} backupConfigs={[]} />);
    expect(screen.getByText('No backup configurations found')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    render(<BackupConfigTable {...mockProps} />);
    const editButtons = screen.getAllByLabelText('Edit');
    fireEvent.click(editButtons[0]);
    expect(mockProps.onEdit).toHaveBeenCalledWith(mockBackupConfigs[0]);
  });

  it('calls onDelete when delete button is clicked', () => {
    render(<BackupConfigTable {...mockProps} />);
    const deleteButtons = screen.getAllByLabelText('Delete');
    fireEvent.click(deleteButtons[0]);
    expect(mockProps.onDelete).toHaveBeenCalledWith(mockBackupConfigs[0]);
  });

  it('calls onBackupNow when backup now button is clicked', () => {
    render(<BackupConfigTable {...mockProps} />);
    const backupNowButtons = screen.getAllByLabelText('Backup Now');
    fireEvent.click(backupNowButtons[0]);
    expect(mockProps.onBackupNow).toHaveBeenCalledWith(mockBackupConfigs[0]);
  });

  it('disables backup now button for inactive configs', () => {
    render(<BackupConfigTable {...mockProps} />);
    const backupNowButtons = screen.getAllByLabelText('Backup Now');

    // First button should be enabled (active config)
    expect(backupNowButtons[0]).not.toBeDisabled();

    // Second button should be disabled (inactive config)
    expect(backupNowButtons[1]).toBeDisabled();
  });
});
