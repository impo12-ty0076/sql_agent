import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Chip,
  Box,
  Tooltip,
  Divider,
  Menu,
  MenuItem,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import DeleteIcon from '@mui/icons-material/Delete';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import ShareIcon from '@mui/icons-material/Share';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import EditIcon from '@mui/icons-material/Edit';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

import { AppDispatch, RootState } from '../../store';
import { setSelectedItem } from '../../store/slices/historySlice';
import { toggleFavorite, deleteHistoryItem, QueryHistoryItem } from '../../services/historyService';

interface HistoryListProps {
  items: QueryHistoryItem[];
}

const HistoryList: React.FC<HistoryListProps> = ({ items }) => {
  const dispatch = useDispatch<AppDispatch>();
  const { selectedItem } = useSelector((state: RootState) => state.history);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [activeItem, setActiveItem] = useState<QueryHistoryItem | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<string | null>(null);

  const handleSelectItem = (item: QueryHistoryItem) => {
    dispatch(setSelectedItem(item));
  };

  const handleToggleFavorite = (e: React.MouseEvent, item: QueryHistoryItem) => {
    e.stopPropagation();
    dispatch(toggleFavorite({ historyId: item.id, favorite: !item.favorite }));
  };

  const handleMenuOpen = (e: React.MouseEvent, item: QueryHistoryItem) => {
    e.stopPropagation();
    setMenuAnchorEl(e.currentTarget as HTMLElement);
    setActiveItem(item);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
    setActiveItem(null);
  };

  const handleDeleteClick = () => {
    if (activeItem) {
      setItemToDelete(activeItem.id);
      setDeleteDialogOpen(true);
      handleMenuClose();
    }
  };

  const handleDeleteConfirm = () => {
    if (itemToDelete) {
      dispatch(deleteHistoryItem(itemToDelete));
      setDeleteDialogOpen(false);
      setItemToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setItemToDelete(null);
  };

  const handleRerunQuery = () => {
    // This would be implemented in a real application
    alert('쿼리 재실행 기능은 아직 구현되지 않았습니다.');
    handleMenuClose();
  };

  const handleShareQuery = () => {
    // This would be implemented in a real application
    alert('쿼리 공유 기능은 아직 구현되지 않았습니다.');
    handleMenuClose();
  };

  const handleEditTags = () => {
    // Select the item and open the detail view
    if (activeItem) {
      dispatch(setSelectedItem(activeItem));
      // In a real implementation, we would also trigger the tag editing mode in the detail view
    }
    handleMenuClose();
  };

  if (items.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography variant="body1" color="text.secondary">
          쿼리 이력이 없습니다
        </Typography>
      </Box>
    );
  }

  return (
    <>
      <List sx={{ width: '100%', bgcolor: 'background.paper', flexGrow: 1, overflow: 'auto' }}>
        {items.map((item, index) => (
          <React.Fragment key={item.id}>
            <ListItem
              alignItems="flex-start"
              selected={selectedItem?.id === item.id}
              onClick={() => handleSelectItem(item)}
              sx={{
                cursor: 'pointer',
                '&:hover': { bgcolor: 'action.hover' },
                py: 1,
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <IconButton
                      edge="start"
                      size="small"
                      onClick={e => handleToggleFavorite(e, item)}
                      color={item.favorite ? 'warning' : 'default'}
                    >
                      {item.favorite ? <StarIcon /> : <StarBorderIcon />}
                    </IconButton>
                    <Typography
                      variant="subtitle1"
                      component="span"
                      noWrap
                      sx={{ maxWidth: '70%' }}
                    >
                      {`쿼리 #${item.query_id.substring(0, 8)}`}
                    </Typography>
                  </Box>
                }
                secondary={
                  <React.Fragment>
                    <Typography
                      component="span"
                      variant="body2"
                      color="text.primary"
                      sx={{ display: 'block', mt: 0.5 }}
                    >
                      {format(new Date(item.created_at), 'yyyy년 MM월 dd일 HH:mm', { locale: ko })}
                    </Typography>
                    <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {item.tags.length > 0 ? (
                        item.tags.map(tag => (
                          <Chip
                            key={tag}
                            label={tag}
                            size="small"
                            onClick={e => e.stopPropagation()}
                          />
                        ))
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          태그 없음
                        </Typography>
                      )}
                    </Box>
                    {item.notes && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{
                          display: 'block',
                          mt: 0.5,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          maxWidth: '100%',
                        }}
                      >
                        {item.notes}
                      </Typography>
                    )}
                  </React.Fragment>
                }
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="more options"
                  onClick={e => handleMenuOpen(e, item)}
                >
                  <MoreVertIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
            {index < items.length - 1 && <Divider component="li" />}
          </React.Fragment>
        ))}
      </List>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={handleRerunQuery}>
          <ListItemIcon>
            <PlayArrowIcon fontSize="small" />
          </ListItemIcon>
          쿼리 재실행
        </MenuItem>
        <MenuItem onClick={handleShareQuery}>
          <ListItemIcon>
            <ShareIcon fontSize="small" />
          </ListItemIcon>
          공유
        </MenuItem>
        <MenuItem onClick={handleEditTags}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          태그 편집
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          삭제
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">쿼리 이력 삭제</DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            이 쿼리 이력을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>취소</Button>
          <Button onClick={handleDeleteConfirm} color="error" autoFocus>
            삭제
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default HistoryList;
