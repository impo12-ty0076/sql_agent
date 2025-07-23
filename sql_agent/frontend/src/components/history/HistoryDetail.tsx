import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Box, 
  Typography, 
  Divider, 
  Button, 
  TextField, 
  Chip, 
  IconButton,
  Paper,
  Tabs,
  Tab,
  Tooltip,
  CircularProgress,
  Autocomplete,
  Snackbar,
  Alert
} from '@mui/material';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import ShareIcon from '@mui/icons-material/Share';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

import { AppDispatch, RootState } from '../../store';
import { 
  QueryHistoryItem, 
  toggleFavorite, 
  updateTags, 
  updateHistoryItem,
  getShareLinks
} from '../../services/historyService';
import api from '../../services/api';
import { QueryDetailsResponse, TagsResponse } from '../../types/api';
import ShareQueryDialog from './ShareQueryDialog';
import SharedQueriesList from './SharedQueriesList';

interface HistoryDetailProps {
  item: QueryHistoryItem;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`history-tabpanel-${index}`}
      aria-labelledby={`history-tab-${index}`}
      {...other}
      style={{ height: 'calc(100% - 48px)', overflow: 'auto' }}
    >
      {value === index && (
        <Box sx={{ p: 2, height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const HistoryDetail: React.FC<HistoryDetailProps> = ({ item }) => {
  const dispatch = useDispatch<AppDispatch>();
  const [tabValue, setTabValue] = useState(0);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState(item.notes || '');
  const [editingTags, setEditingTags] = useState(false);
  const [tags, setTags] = useState<string[]>(item.tags || []);
  const [availableTags, setAvailableTags] = useState<string[]>([
    '중요', '보고서', '매출', '고객', '제품', '분석', '월간', '분기', '연간'
  ]); // 실제로는 API에서 가져와야 함
  const [queryDetails, setQueryDetails] = useState<QueryDetailsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  
  useEffect(() => {
    setNotes(item.notes || '');
    setTags(item.tags || []);
    
    // Fetch query details when item changes
    const fetchQueryDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get<QueryDetailsResponse>(`/api/query/${item.query_id}`);
        setQueryDetails(response.data);
      } catch (err: any) {
        setError(err.response?.data?.message || '쿼리 상세 정보를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    // Fetch available tags
    const fetchAvailableTags = async () => {
      try {
        const response = await api.get<TagsResponse>('/api/query-history/tags');
        if (response.data && Array.isArray(response.data.tags)) {
          setAvailableTags(response.data.tags);
        }
      } catch (err) {
        console.error('Failed to fetch available tags:', err);
      }
    };
    
    fetchQueryDetails();
    fetchAvailableTags();
  }, [item]);
  
  const handleToggleFavorite = () => {
    dispatch(toggleFavorite({ historyId: item.id, favorite: !item.favorite }));
  };
  
  const handleSaveNotes = () => {
    dispatch(updateHistoryItem({ 
      historyId: item.id, 
      data: { notes } 
    }));
    setEditingNotes(false);
    showSnackbar('메모가 저장되었습니다.', 'success');
  };
  
  const handleSaveTags = () => {
    dispatch(updateTags({ 
      historyId: item.id, 
      tags 
    }));
    setEditingTags(false);
    showSnackbar('태그가 저장되었습니다.', 'success');
  };
  
  const handleRerunQuery = async () => {
    if (!queryDetails) return;
    
    try {
      // Navigate to query page and set the query
      // This is a placeholder - actual implementation would depend on your app's routing and state management
      showSnackbar('쿼리 재실행 기능은 아직 구현되지 않았습니다.', 'error');
    } catch (err) {
      console.error('Failed to rerun query:', err);
      showSnackbar('쿼리 재실행에 실패했습니다.', 'error');
    }
  };
  
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  const shareLinks = useSelector((state: RootState) => 
    state.history.shareLinks[item.id] || []
  );
  const shareLinksLoading = useSelector((state: RootState) => state.history.shareLinksLoading);
  const shareLinksError = useSelector((state: RootState) => state.history.shareLinksError);
  
  useEffect(() => {
    // Fetch share links for this history item
    dispatch(getShareLinks(item.id));
  }, [dispatch, item.id]);
  
  const handleShareQuery = () => {
    setShareDialogOpen(true);
  };
  
  const handleCloseShareDialog = () => {
    setShareDialogOpen(false);
    // Refresh share links after dialog closes
    dispatch(getShareLinks(item.id));
  };
  
  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };
  
  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };
  
  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" component="h2">
          쿼리 상세 정보
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={item.favorite ? "즐겨찾기 해제" : "즐겨찾기 추가"}>
            <IconButton onClick={handleToggleFavorite} color={item.favorite ? "warning" : "default"}>
              {item.favorite ? <StarIcon /> : <StarBorderIcon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="공유">
            <IconButton onClick={handleShareQuery} color="primary">
              <ShareIcon />
            </IconButton>
          </Tooltip>
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<PlayArrowIcon />}
            onClick={handleRerunQuery}
            disabled={loading || !queryDetails}
          >
            쿼리 재실행
          </Button>
        </Box>
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          생성일: {format(new Date(item.created_at), 'yyyy년 MM월 dd일 HH:mm:ss', { locale: ko })}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          마지막 수정일: {format(new Date(item.updated_at), 'yyyy년 MM월 dd일 HH:mm:ss', { locale: ko })}
        </Typography>
      </Box>
      
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1">태그</Typography>
          {!editingTags ? (
            <IconButton size="small" onClick={() => setEditingTags(true)}>
              <EditIcon fontSize="small" />
            </IconButton>
          ) : (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton size="small" onClick={handleSaveTags} color="primary">
                <SaveIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" onClick={() => {
                setEditingTags(false);
                setTags(item.tags || []);
              }}>
                <CancelIcon fontSize="small" />
              </IconButton>
            </Box>
          )}
        </Box>
        
        {!editingTags ? (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {item.tags.length > 0 ? (
              item.tags.map((tag) => (
                <Chip key={tag} label={tag} size="small" />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                태그 없음
              </Typography>
            )}
          </Box>
        ) : (
          <Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
              {tags.map((tag) => (
                <Chip 
                  key={tag} 
                  label={tag} 
                  size="small" 
                  onDelete={() => handleRemoveTag(tag)} 
                />
              ))}
            </Box>
            <Autocomplete
              multiple
              id="tags-input"
              options={availableTags.filter(tag => !tags.includes(tag))}
              freeSolo
              renderTags={() => null}
              value={[]}
              onChange={(_, newValue) => {
                if (newValue.length > 0) {
                  const newTag = newValue[newValue.length - 1];
                  if (newTag && !tags.includes(newTag)) {
                    setTags([...tags, newTag]);
                  }
                }
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  variant="outlined"
                  size="small"
                  placeholder="태그 추가"
                  fullWidth
                />
              )}
            />
          </Box>
        )}
      </Box>
      
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1">메모</Typography>
          {!editingNotes ? (
            <IconButton size="small" onClick={() => setEditingNotes(true)}>
              <EditIcon fontSize="small" />
            </IconButton>
          ) : (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton size="small" onClick={handleSaveNotes} color="primary">
                <SaveIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" onClick={() => {
                setEditingNotes(false);
                setNotes(item.notes || '');
              }}>
                <CancelIcon fontSize="small" />
              </IconButton>
            </Box>
          )}
        </Box>
        
        {!editingNotes ? (
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
            {item.notes || '메모 없음'}
          </Typography>
        ) : (
          <TextField
            multiline
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            fullWidth
            placeholder="메모를 입력하세요"
          />
        )}
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ mb: 2 }}>
        <SharedQueriesList 
          historyId={item.id}
          shareLinks={shareLinks}
          loading={shareLinksLoading}
          error={shareLinksError}
        />
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="query details tabs">
            <Tab label="자연어 질의" id="history-tab-0" aria-controls="history-tabpanel-0" />
            <Tab label="SQL" id="history-tab-1" aria-controls="history-tabpanel-1" />
            <Tab label="결과" id="history-tab-2" aria-controls="history-tabpanel-2" />
          </Tabs>
        </Box>
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Typography color="error">{error}</Typography>
          </Box>
        ) : (
          <>
            <TabPanel value={tabValue} index={0}>
              {queryDetails?.natural_language ? (
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {queryDetails.natural_language}
                </Typography>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  자연어 질의 정보가 없습니다
                </Typography>
              )}
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              {queryDetails?.generated_sql ? (
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2, 
                    bgcolor: 'grey.100', 
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                    overflowX: 'auto'
                  }}
                >
                  {queryDetails.generated_sql}
                </Paper>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  SQL 정보가 없습니다
                </Typography>
              )}
            </TabPanel>
            
            <TabPanel value={tabValue} index={2}>
              {queryDetails?.result ? (
                <Box sx={{ height: '100%', overflow: 'auto' }}>
                  {/* 결과 데이터 표시 - 실제 구현은 결과 데이터 형식에 따라 달라질 수 있음 */}
                  <Typography variant="body2">
                    결과 데이터가 있습니다. 실제 구현은 데이터 형식에 따라 달라질 수 있습니다.
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  결과 정보가 없습니다
                </Typography>
              )}
            </TabPanel>
          </>
        )}
      </Box>
      
      {/* 공유 다이얼로그 */}
      <ShareQueryDialog 
        open={shareDialogOpen} 
        onClose={handleCloseShareDialog} 
        historyId={item.id}
        existingShareLink={shareLinks.length > 0 ? {
          id: shareLinks[0].id,
          link: shareLinks[0].share_link,
          expiresAt: shareLinks[0].expires_at,
          allowedUsers: shareLinks[0].allowed_users
        } : undefined}
      />
      
      {/* 알림 스낵바 */}
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

export default HistoryDetail;