import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Box, 
  Paper, 
  TextField, 
  FormControlLabel, 
  Checkbox, 
  Button, 
  Chip,
  Autocomplete,
  IconButton,
  InputAdornment,
  Typography,
  Grid,
  Collapse,
  Tooltip,
  Badge
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import SearchIcon from '@mui/icons-material/Search';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

import { AppDispatch, RootState } from '../../store';
import { setFilters, resetFilters } from '../../store/slices/historySlice';
import api from '../../services/api';

const HistoryFilters: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { filters } = useSelector((state: RootState) => state.history);
  
  const [expanded, setExpanded] = useState<boolean>(false);
  const [startDate, setStartDate] = useState<Date | null>(filters.start_date ? new Date(filters.start_date) : null);
  const [endDate, setEndDate] = useState<Date | null>(filters.end_date ? new Date(filters.end_date) : null);
  const [favoriteOnly, setFavoriteOnly] = useState<boolean>(filters.favorite_only || false);
  const [selectedTags, setSelectedTags] = useState<string[]>(filters.tags || []);
  const [searchText, setSearchText] = useState<string>(filters.search_text || '');
  const [availableTags, setAvailableTags] = useState<string[]>([
    '중요', '보고서', '매출', '고객', '제품', '분석', '월간', '분기', '연간'
  ]);
  
  // Count active filters
  const activeFilterCount = [
    startDate !== null,
    endDate !== null,
    favoriteOnly,
    selectedTags.length > 0,
    searchText.trim() !== ''
  ].filter(Boolean).length;
  
  useEffect(() => {
    // Fetch available tags from API
    const fetchTags = async () => {
      try {
        const response = await api.get('/api/query-history/tags');
        if (response.data && Array.isArray(response.data.tags)) {
          setAvailableTags(response.data.tags);
        }
      } catch (err) {
        console.error('Failed to fetch tags:', err);
      }
    };
    
    fetchTags();
  }, []);
  
  const handleApplyFilters = () => {
    dispatch(setFilters({
      favorite_only: favoriteOnly,
      tags: selectedTags,
      start_date: startDate ? format(startDate, 'yyyy-MM-dd') : undefined,
      end_date: endDate ? format(endDate, 'yyyy-MM-dd') : undefined,
      search_text: searchText.trim() || undefined,
    }));
  };
  
  const handleResetFilters = () => {
    setStartDate(null);
    setEndDate(null);
    setFavoriteOnly(false);
    setSelectedTags([]);
    setSearchText('');
    dispatch(resetFilters());
  };
  
  const toggleExpanded = () => {
    setExpanded(!expanded);
  };

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title={`${activeFilterCount}개의 필터 적용됨`}>
            <Badge badgeContent={activeFilterCount} color="primary" sx={{ mr: 1 }}>
              <FilterListIcon />
            </Badge>
          </Tooltip>
          <Typography variant="h6">필터</Typography>
        </Box>
        
        <IconButton onClick={toggleExpanded}>
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      
      {/* 검색 필드는 항상 표시 */}
      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          size="small"
          label="검색"
          placeholder="쿼리 내용, 메모 검색"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            endAdornment: searchText && (
              <InputAdornment position="end">
                <IconButton
                  size="small"
                  onClick={() => setSearchText('')}
                  edge="end"
                >
                  <ClearIcon fontSize="small" />
                </IconButton>
              </InputAdornment>
            )
          }}
        />
      </Box>
      
      <Collapse in={expanded}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <DatePicker
                  label="시작일"
                  value={startDate}
                  onChange={(newValue) => setStartDate(newValue)}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      size: "small",
                      InputProps: {
                        endAdornment: startDate && (
                          <InputAdornment position="end">
                            <IconButton
                              size="small"
                              onClick={() => setStartDate(null)}
                              edge="end"
                            >
                              <ClearIcon fontSize="small" />
                            </IconButton>
                          </InputAdornment>
                        )
                      }
                    }
                  }}
                />
                <DatePicker
                  label="종료일"
                  value={endDate}
                  onChange={(newValue) => setEndDate(newValue)}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      size: "small",
                      InputProps: {
                        endAdornment: endDate && (
                          <InputAdornment position="end">
                            <IconButton
                              size="small"
                              onClick={() => setEndDate(null)}
                              edge="end"
                            >
                              <ClearIcon fontSize="small" />
                            </IconButton>
                          </InputAdornment>
                        )
                      }
                    }
                  }}
                />
              </Box>
            </LocalizationProvider>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={favoriteOnly} 
                    onChange={(e) => setFavoriteOnly(e.target.checked)}
                  />
                }
                label="즐겨찾기만 보기"
              />
              
              <Autocomplete
                multiple
                id="tags-filter"
                options={availableTags}
                value={selectedTags}
                onChange={(_, newValue) => setSelectedTags(newValue)}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option}
                      {...getTagProps({ index })}
                      key={option}
                    />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="outlined"
                    label="태그"
                    placeholder="태그 선택"
                    size="small"
                    fullWidth
                  />
                )}
                size="small"
                sx={{ flexGrow: 1 }}
              />
            </Box>
          </Grid>
        </Grid>
      </Collapse>
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, gap: 1 }}>
        <Button 
          variant="outlined" 
          onClick={handleResetFilters}
          disabled={activeFilterCount === 0}
        >
          초기화
        </Button>
        <Button 
          variant="contained" 
          onClick={handleApplyFilters}
        >
          적용
        </Button>
      </Box>
    </Paper>
  );
};

export default HistoryFilters;