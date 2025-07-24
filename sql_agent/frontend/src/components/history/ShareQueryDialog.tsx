import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  TextField,
  Box,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  FormHelperText,
  CircularProgress,
  Snackbar,
  Alert,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store';
import { createShareLink, updateShareLink, deleteShareLink } from '../../services/historyService';

interface ShareQueryDialogProps {
  open: boolean;
  onClose: () => void;
  historyId: string;
  existingShareLink?: {
    id: string;
    link: string;
    expiresAt?: string;
    allowedUsers?: string[];
  };
}

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const ShareQueryDialog: React.FC<ShareQueryDialogProps> = ({
  open,
  onClose,
  historyId,
  existingShareLink,
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const [shareLink, setShareLink] = useState(existingShareLink?.link || '');
  const [shareExpiry, setShareExpiry] = useState(existingShareLink?.expiresAt ? '7' : '7'); // Default 7 days
  const [allowedUsers, setAllowedUsers] = useState<string[]>(existingShareLink?.allowedUsers || []);
  const [newUser, setNewUser] = useState('');
  const [loading, setLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  const handleCreateOrUpdateShareLink = async () => {
    setLoading(true);
    try {
      if (existingShareLink) {
        // Update existing share link
        const result = await dispatch(
          updateShareLink({
            shareId: existingShareLink.id,
            expiresInDays: parseInt(shareExpiry, 10),
            allowedUsers,
          })
        ).unwrap();

        setShareLink(result.share_link);
        showSnackbar('공유 링크가 업데이트되었습니다.', 'success');
      } else {
        // Create new share link
        const result = await dispatch(
          createShareLink({
            historyId,
            expiresInDays: parseInt(shareExpiry, 10),
            allowedUsers: allowedUsers.length > 0 ? allowedUsers : undefined,
          })
        ).unwrap();

        setShareLink(result.share_link);
        showSnackbar('공유 링크가 생성되었습니다.', 'success');
      }
    } catch (error) {
      console.error('Failed to create/update share link:', error);
      showSnackbar('공유 링크 생성/업데이트에 실패했습니다.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteShareLink = async () => {
    if (!existingShareLink) return;

    setLoading(true);
    try {
      await dispatch(deleteShareLink(existingShareLink.id)).unwrap();
      setShareLink('');
      showSnackbar('공유 링크가 삭제되었습니다.', 'success');
      onClose();
    } catch (error) {
      console.error('Failed to delete share link:', error);
      showSnackbar('공유 링크 삭제에 실패했습니다.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(shareLink);
    showSnackbar('링크가 클립보드에 복사되었습니다.', 'success');
  };

  const handleAddUser = () => {
    if (newUser && !allowedUsers.includes(newUser)) {
      setAllowedUsers([...allowedUsers, newUser]);
      setNewUser('');
    }
  };

  const handleRemoveUser = (userToRemove: string) => {
    setAllowedUsers(allowedUsers.filter(user => user !== userToRemove));
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
    <>
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>쿼리 공유</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            이 쿼리를 다른 사용자와 공유할 수 있습니다. 링크 만료 기간을 선택하고 특정 사용자에게만
            접근을 허용할 수 있습니다.
          </DialogContentText>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel id="expiry-select-label">만료 기간</InputLabel>
              <Select
                labelId="expiry-select-label"
                id="expiry-select"
                value={shareExpiry}
                label="만료 기간"
                onChange={e => setShareExpiry(e.target.value)}
                disabled={loading}
              >
                <MenuItem value="1">1일</MenuItem>
                <MenuItem value="7">7일</MenuItem>
                <MenuItem value="30">30일</MenuItem>
                <MenuItem value="90">90일</MenuItem>
                <MenuItem value="365">1년</MenuItem>
                <MenuItem value="0">만료 없음</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel id="allowed-users-label">접근 허용 사용자</InputLabel>
              <Select
                labelId="allowed-users-label"
                id="allowed-users-select"
                multiple
                value={allowedUsers}
                input={<OutlinedInput id="select-multiple-chip" label="접근 허용 사용자" />}
                renderValue={selected => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map(value => (
                      <Chip key={value} label={value} onDelete={() => handleRemoveUser(value)} />
                    ))}
                  </Box>
                )}
                MenuProps={MenuProps}
                disabled={loading}
              >
                {allowedUsers.map(user => (
                  <MenuItem key={user} value={user}>
                    {user}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>비워두면 링크가 있는 모든 사용자가 접근할 수 있습니다</FormHelperText>
            </FormControl>

            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                label="사용자 추가"
                value={newUser}
                onChange={e => setNewUser(e.target.value)}
                fullWidth
                placeholder="사용자 이메일 또는 ID 입력"
                disabled={loading}
              />
              <Button variant="outlined" onClick={handleAddUser} disabled={!newUser || loading}>
                추가
              </Button>
            </Box>

            {shareLink && (
              <Box sx={{ mt: 2 }}>
                <TextField
                  label="공유 링크"
                  value={shareLink}
                  fullWidth
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <IconButton onClick={handleCopyShareLink} edge="end" disabled={loading}>
                        <ContentCopyIcon />
                      </IconButton>
                    ),
                  }}
                />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            닫기
          </Button>

          {existingShareLink && (
            <Button onClick={handleDeleteShareLink} color="error" disabled={loading}>
              {loading ? <CircularProgress size={24} /> : '링크 삭제'}
            </Button>
          )}

          <Button
            onClick={handleCreateOrUpdateShareLink}
            variant="contained"
            color="primary"
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} />
            ) : existingShareLink ? (
              '링크 업데이트'
            ) : (
              '링크 생성'
            )}
          </Button>
        </DialogActions>
      </Dialog>

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
    </>
  );
};

export default ShareQueryDialog;
