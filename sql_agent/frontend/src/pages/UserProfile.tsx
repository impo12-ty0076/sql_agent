import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import {
  Box,
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Divider,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Avatar,
  Card,
  CardHeader,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Person,
  Settings as SettingsIcon,
  Edit,
  Visibility,
  VisibilityOff,
  Save,
  Cancel,
} from '@mui/icons-material';
import { RootState } from '../store';
import { Database } from '../store/slices/dbSlice';
import Layout from '../components/layout/Layout';
import useAuth from '../hooks/useAuth';

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
      id={`profile-tabpanel-${index}`}
      aria-labelledby={`profile-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const UserProfile: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Profile form state
  const [email, setEmail] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Preferences form state
  const [defaultDb, setDefaultDb] = useState('');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [resultsPerPage, setResultsPerPage] = useState(50);

  const { user, updateProfile, changePassword } = useAuth();
  const { databases } = useSelector((state: RootState) => state.db as { databases: Database[] });

  useEffect(() => {
    if (user) {
      setEmail(user.email || '');

      // Load user preferences
      if (user.preferences) {
        setDefaultDb(user.preferences.defaultDb || '');
        setTheme(user.preferences.theme || 'light');
        setResultsPerPage(user.preferences.resultsPerPage || 50);
      }
    }
  }, [user]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    // Clear messages when switching tabs
    setSuccess('');
    setError('');
    setEditMode(false);
  };

  const toggleEditMode = () => {
    setEditMode(!editMode);
    setSuccess('');
    setError('');
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const validateProfileForm = () => {
    if (newPassword && newPassword.length < 8) {
      setError('새 비밀번호는 8자 이상이어야 합니다');
      return false;
    }

    if (newPassword && newPassword !== confirmPassword) {
      setError('새 비밀번호와 확인 비밀번호가 일치하지 않습니다');
      return false;
    }

    return true;
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateProfileForm()) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Update profile information
      if (user) {
        const result = await updateProfile({
          ...user,
          email,
        });

        if (!result.success) {
          throw new Error(result.error);
        }
      }

      // Change password if provided
      if (currentPassword && newPassword) {
        const passwordResult = await changePassword(currentPassword, newPassword);

        if (!passwordResult.success) {
          throw new Error(passwordResult.error);
        }
      }

      setSuccess('프로필이 성공적으로 업데이트되었습니다');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setEditMode(false);
    } catch (err: any) {
      setError(err.message || '프로필 업데이트 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handlePreferencesSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Update user preferences
      if (user) {
        const result = await updateProfile({
          ...user,
          preferences: {
            defaultDb,
            theme,
            resultsPerPage,
          },
        });

        if (!result.success) {
          throw new Error(result.error);
        }
      }

      setSuccess('환경설정이 성공적으로 업데이트되었습니다');
      setEditMode(false);
    } catch (err: any) {
      setError(err.message || '환경설정 업데이트 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="사용자 프로필">
      <Container maxWidth="md">
        <Box sx={{ mb: 4 }}>
          <Card>
            <CardHeader
              avatar={
                <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </Avatar>
              }
              title={
                <Typography variant="h5" component="h1">
                  {user?.username || '사용자'}
                </Typography>
              }
              subheader={
                <Typography variant="subtitle1" color="text.secondary">
                  {user?.role === 'admin' ? '관리자' : '사용자'}
                </Typography>
              }
              action={
                <IconButton onClick={toggleEditMode} color={editMode ? 'primary' : 'default'}>
                  <Edit />
                </IconButton>
              }
            />
          </Card>
        </Box>

        <Paper elevation={3}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              aria-label="profile tabs"
              variant="fullWidth"
            >
              <Tab
                label="프로필 정보"
                id="profile-tab-0"
                aria-controls="profile-tabpanel-0"
                icon={<Person />}
                iconPosition="start"
              />
              <Tab
                label="환경설정"
                id="profile-tab-1"
                aria-controls="profile-tabpanel-1"
                icon={<SettingsIcon />}
                iconPosition="start"
              />
            </Tabs>
          </Box>

          {/* Profile Information Tab */}
          <TabPanel value={tabValue} index={0}>
            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {success}
              </Alert>
            )}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleProfileSubmit} noValidate>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    disabled
                    label="사용자명"
                    value={user?.username || ''}
                    variant="outlined"
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    required
                    label="이메일"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    disabled={!editMode || loading}
                    variant="outlined"
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    disabled
                    label="역할"
                    value={user?.role === 'admin' ? '관리자' : '사용자'}
                    variant="outlined"
                  />
                </Grid>

                {editMode && (
                  <>
                    <Grid item xs={12}>
                      <Divider sx={{ my: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          비밀번호 변경
                        </Typography>
                      </Divider>
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        type={showPassword ? 'text' : 'password'}
                        label="현재 비밀번호"
                        value={currentPassword}
                        onChange={e => setCurrentPassword(e.target.value)}
                        disabled={loading}
                        variant="outlined"
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                aria-label="toggle password visibility"
                                onClick={togglePasswordVisibility}
                                edge="end"
                              >
                                {showPassword ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        type={showPassword ? 'text' : 'password'}
                        label="새 비밀번호"
                        value={newPassword}
                        onChange={e => setNewPassword(e.target.value)}
                        disabled={loading}
                        variant="outlined"
                        helperText="8자 이상 입력해주세요"
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        type={showPassword ? 'text' : 'password'}
                        label="새 비밀번호 확인"
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        disabled={loading}
                        variant="outlined"
                        error={newPassword !== confirmPassword && confirmPassword !== ''}
                        helperText={
                          newPassword !== confirmPassword && confirmPassword !== ''
                            ? '비밀번호가 일치하지 않습니다'
                            : ' '
                        }
                      />
                    </Grid>
                  </>
                )}

                {editMode && (
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                      <Button
                        type="submit"
                        variant="contained"
                        disabled={loading}
                        startIcon={loading ? <CircularProgress size={20} /> : <Save />}
                      >
                        저장
                      </Button>
                      <Button
                        variant="outlined"
                        onClick={toggleEditMode}
                        disabled={loading}
                        startIcon={<Cancel />}
                      >
                        취소
                      </Button>
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Box>
          </TabPanel>

          {/* Preferences Tab */}
          <TabPanel value={tabValue} index={1}>
            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {success}
              </Alert>
            )}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handlePreferencesSubmit} noValidate>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <FormControl fullWidth variant="outlined">
                    <InputLabel id="default-db-label">기본 데이터베이스</InputLabel>
                    <Select
                      labelId="default-db-label"
                      value={defaultDb}
                      label="기본 데이터베이스"
                      onChange={e => setDefaultDb(e.target.value)}
                      disabled={!editMode || loading}
                    >
                      <MenuItem value="">
                        <em>선택 안함</em>
                      </MenuItem>
                      {databases?.map(db => (
                        <MenuItem key={db.id} value={db.id}>
                          {db.name} ({db.type})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={theme === 'dark'}
                          onChange={e => setTheme(e.target.checked ? 'dark' : 'light')}
                          disabled={!editMode || loading}
                          color="primary"
                        />
                      }
                      label={
                        <Typography variant="body1">
                          다크 모드 {theme === 'dark' ? '활성화' : '비활성화'}
                        </Typography>
                      }
                    />
                  </Paper>
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth variant="outlined">
                    <InputLabel id="results-per-page-label">페이지당 결과 수</InputLabel>
                    <Select
                      labelId="results-per-page-label"
                      value={resultsPerPage}
                      label="페이지당 결과 수"
                      onChange={e => setResultsPerPage(Number(e.target.value))}
                      disabled={!editMode || loading}
                    >
                      <MenuItem value={10}>10</MenuItem>
                      <MenuItem value={25}>25</MenuItem>
                      <MenuItem value={50}>50</MenuItem>
                      <MenuItem value={100}>100</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                {editMode && (
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                      <Button
                        type="submit"
                        variant="contained"
                        disabled={loading}
                        startIcon={loading ? <CircularProgress size={20} /> : <Save />}
                      >
                        저장
                      </Button>
                      <Button
                        variant="outlined"
                        onClick={toggleEditMode}
                        disabled={loading}
                        startIcon={<Cancel />}
                      >
                        취소
                      </Button>
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Box>
          </TabPanel>
        </Paper>
      </Container>
    </Layout>
  );
};

export default UserProfile;
