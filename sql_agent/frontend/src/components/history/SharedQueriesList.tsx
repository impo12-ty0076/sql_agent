import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  Tooltip,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Alert,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import EditIcon from '@mui/icons-material/Edit';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store';
import { deleteShareLink, getShareLinks, ShareLink } from '../../services/historyService';
import ShareQueryDialog from './ShareQueryDialog';

interface SharedQueriesListProps {
  historyId: string;
  shareLinks: ShareLink[];
  loading: boolean;
  error: string | null;
}

const SharedQueriesList: React.FC<SharedQueriesListProps> = ({
  historyId,
  shareLinks,
  loading,
  error,
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedShareLink, setSelectedShareLink] = useState<ShareLink | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [shareToDelete, setShareToDelete] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  const handleEditShare = (shareLink: ShareLink) => {
    setSelectedShareLink(shareLink);
    setEditDialogOpen(true);
  };

  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setSelectedShareLink(null);
    // Refresh share links
    dispatch(getShareLinks(historyId));
  };

  const handleDeleteClick = (shareId: string) => {
    setShareToDelete(shareId);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!shareToDelete) return;

    try {
      await dispatch(deleteShareLink(shareToDelete)).unwrap();
      showSnackbar('공유 링크가 삭제되었습니다.', 'success');
    } catch (error) {
      console.error('Failed to delete share link:', error);
      showSnackbar('공유 링크 삭제에 실패했습니다.', 'error');
    } finally {
      setDeleteDialogOpen(false);
      setShareToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setShareToDelete(null);
  };

  const handleCopyLink = (link: string) => {
    navigator.clipboard.writeText(link);
    showSnackbar('링크가 클립보드에 복사되었습니다.', 'success');
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        공유된 링크
      </Typography>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress size={24} />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : shareLinks.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
          이 쿼리에 대한 공유 링크가 없습니다.
        </Typography>
      ) : (
        <Paper variant="outlined" sx={{ mb: 2 }}>
          <List dense>
            {shareLinks.map((shareLink, index) => (
              <React.Fragment key={shareLink.id}>
                {index > 0 && <Divider />}
                <ListItem>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" noWrap sx={{ maxWidth: '200px' }}>
                          {shareLink.share_link}
                        </Typography>
                        <Tooltip title="링크 복사">
                          <IconButton
                            size="small"
                            onClick={() => handleCopyLink(shareLink.share_link)}
                          >
                            <ContentCopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          생성일:{' '}
                          {format(new Date(shareLink.created_at), 'yyyy년 MM월 dd일', {
                            locale: ko,
                          })}
                        </Typography>
                        {shareLink.expires_at && (
                          <Typography variant="caption" display="block">
                            만료일:{' '}
                            {format(new Date(shareLink.expires_at), 'yyyy년 MM월 dd일', {
                              locale: ko,
                            })}
                          </Typography>
                        )}
                        {shareLink.allowed_users && shareLink.allowed_users.length > 0 && (
                          <Typography variant="caption" display="block">
                            허용된 사용자: {shareLink.allowed_users.join(', ')}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Tooltip title="수정">
                      <IconButton
                        edge="end"
                        aria-label="edit"
                        onClick={() => handleEditShare(shareLink)}
                        size="small"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="삭제">
                      <IconButton
                        edge="end"
                        aria-label="delete"
                        onClick={() => handleDeleteClick(shareLink.id)}
                        size="small"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </ListItemSecondaryAction>
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}

      {/* Edit Share Dialog */}
      {selectedShareLink && (
        <ShareQueryDialog
          open={editDialogOpen}
          onClose={handleCloseEditDialog}
          historyId={historyId}
          existingShareLink={{
            id: selectedShareLink.id,
            link: selectedShareLink.share_link,
            expiresAt: selectedShareLink.expires_at,
            allowedUsers: selectedShareLink.allowed_users,
          }}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleCancelDelete}>
        <DialogTitle>공유 링크 삭제</DialogTitle>
        <DialogContent>
          <DialogContentText>
            이 공유 링크를 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>취소</Button>
          <Button onClick={handleConfirmDelete} color="error" autoFocus>
            삭제
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SharedQueriesList;
