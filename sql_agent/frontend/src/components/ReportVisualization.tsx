import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  CardMedia,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Button
} from '@mui/material';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import DownloadIcon from '@mui/icons-material/Download';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

const ReportVisualization: React.FC = () => {
  const { currentReport, error } = useSelector((state: RootState) => state.report);
  
  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" color="error" gutterBottom>
          리포트 생성 오류
        </Typography>
        <Typography variant="body2">
          {error}
        </Typography>
      </Paper>
    );
  }
  
  if (!currentReport) {
    return (
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="body1" align="center" sx={{ py: 4 }}>
          리포트가 생성되지 않았습니다. 쿼리를 실행하고 리포트 생성 옵션을 활성화하세요.
        </Typography>
      </Paper>
    );
  }
  
  const handleDownloadImage = (imageData: string, title: string) => {
    const link = document.createElement('a');
    link.href = imageData;
    link.download = `${title.replace(/\s+/g, '_').toLowerCase()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  const handleDownloadReport = () => {
    // Create a simple HTML report
    let reportHtml = `
      <html>
      <head>
        <title>데이터 분석 리포트</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          h1 { color: #333; }
          .visualization { margin-bottom: 30px; }
          .insights { background-color: #f5f5f5; padding: 20px; border-radius: 5px; }
          img { max-width: 100%; border: 1px solid #ddd; }
        </style>
      </head>
      <body>
        <h1>데이터 분석 리포트</h1>
        <p>생성 시간: ${new Date(currentReport.createdAt).toLocaleString()}</p>
    `;
    
    // Add visualizations
    if (currentReport.visualizations.length > 0) {
      reportHtml += '<h2>시각화</h2>';
      currentReport.visualizations.forEach(viz => {
        reportHtml += `
          <div class="visualization">
            <h3>${viz.title}</h3>
            ${viz.description ? `<p>${viz.description}</p>` : ''}
            <img src="${viz.imageData}" alt="${viz.title}" />
          </div>
        `;
      });
    }
    
    // Add insights
    if (currentReport.insights.length > 0) {
      reportHtml += '<h2>주요 인사이트</h2>';
      reportHtml += '<div class="insights"><ul>';
      currentReport.insights.forEach(insight => {
        reportHtml += `<li>${insight}</li>`;
      });
      reportHtml += '</ul></div>';
    }
    
    reportHtml += '</body></html>';
    
    // Create and download the HTML file
    const blob = new Blob([reportHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'data_analysis_report.html';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">데이터 분석 리포트</Typography>
        <Button 
          variant="outlined" 
          startIcon={<DownloadIcon />}
          onClick={handleDownloadReport}
        >
          리포트 다운로드
        </Button>
      </Box>
      
      {/* Visualizations */}
      {currentReport.visualizations.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="subtitle1" gutterBottom>
            시각화
          </Typography>
          <Grid container spacing={3}>
            {currentReport.visualizations.map((viz) => (
              <Grid item xs={12} md={6} key={viz.id}>
                <Card>
                  <CardMedia
                    component="img"
                    image={viz.imageData}
                    alt={viz.title}
                    sx={{ maxHeight: 300, objectFit: 'contain' }}
                  />
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {viz.title}
                    </Typography>
                    {viz.description && (
                      <Typography variant="body2" color="text.secondary">
                        {viz.description}
                      </Typography>
                    )}
                    <Button 
                      size="small" 
                      sx={{ mt: 1 }}
                      onClick={() => handleDownloadImage(viz.imageData, viz.title)}
                    >
                      이미지 다운로드
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
      
      {/* Insights */}
      {currentReport.insights.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle1" gutterBottom>
            주요 인사이트
          </Typography>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <List>
              {currentReport.insights.map((insight, index) => (
                <ListItem key={index} alignItems="flex-start">
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <LightbulbIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={insight} />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      )}
    </Box>
  );
};

export default ReportVisualization;