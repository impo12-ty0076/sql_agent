import React from 'react';
import {
  FormControlLabel,
  Switch,
  FormGroup,
  Typography,
  Box,
  Checkbox,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  SelectChangeEvent,
} from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { toggleReportGeneration, updateReportOptions } from '../store/slices/reportSlice';

const VISUALIZATION_TYPES = [
  { value: 'bar', label: '막대 그래프' },
  { value: 'line', label: '선 그래프' },
  { value: 'pie', label: '파이 차트' },
  { value: 'scatter', label: '산점도' },
  { value: 'heatmap', label: '히트맵' },
];

const ReportToggle: React.FC = () => {
  const dispatch = useDispatch();
  const { reportGenerationEnabled, reportGenerationOptions } = useSelector(
    (state: RootState) => state.report
  );

  const handleToggleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(toggleReportGeneration(event.target.checked));
  };

  const handleInsightsChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(updateReportOptions({ includeInsights: event.target.checked }));
  };

  const handleVisualizationTypesChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value as string[];
    dispatch(updateReportOptions({ visualizationTypes: value }));
  };

  return (
    <Box sx={{ mb: 2 }}>
      <FormGroup>
        <FormControlLabel
          control={
            <Switch
              checked={reportGenerationEnabled}
              onChange={handleToggleChange}
              color="primary"
            />
          }
          label={
            <Typography variant="body1" fontWeight="medium">
              리포트 생성 활성화
            </Typography>
          }
        />

        {reportGenerationEnabled && (
          <Box sx={{ mt: 2, pl: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              리포트 옵션
            </Typography>

            <FormControlLabel
              control={
                <Checkbox
                  checked={reportGenerationOptions.includeInsights}
                  onChange={handleInsightsChange}
                  size="small"
                />
              }
              label="인사이트 포함"
            />

            <FormControl sx={{ mt: 1, width: '100%' }} size="small">
              <InputLabel id="visualization-types-label">시각화 유형</InputLabel>
              <Select
                labelId="visualization-types-label"
                id="visualization-types"
                multiple
                value={reportGenerationOptions.visualizationTypes}
                onChange={handleVisualizationTypesChange}
                input={<OutlinedInput label="시각화 유형" />}
                renderValue={selected => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map(value => {
                      const type = VISUALIZATION_TYPES.find(t => t.value === value);
                      return <Chip key={value} label={type?.label || value} size="small" />;
                    })}
                  </Box>
                )}
              >
                {VISUALIZATION_TYPES.map(type => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        )}
      </FormGroup>
    </Box>
  );
};

export default ReportToggle;
