import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Link,
  InputAdornment,
  IconButton,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import { Visibility, VisibilityOff, LockOutlined } from '@mui/icons-material';
import useAuth from '../hooks/useAuth';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState({ username: '', password: '' });

  const navigate = useNavigate();
  const { isAuthenticated, loading, error, login } = useAuth();

  useEffect(() => {
    // If already authenticated, redirect to dashboard
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const validateForm = (): boolean => {
    let valid = true;
    const errors = { username: '', password: '' };

    if (!username.trim()) {
      errors.username = '사용자명을 입력해주세요';
      valid = false;
    }

    if (!password) {
      errors.password = '비밀번호를 입력해주세요';
      valid = false;
    } else if (password.length < 6) {
      errors.password = '비밀번호는 최소 6자 이상이어야 합니다';
      valid = false;
    }

    setFormErrors(errors);
    return valid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    const result = await login(username, password);

    if (result.success) {
      // Login successful, navigation is handled in the useAuth hook
    } else {
      // Error is handled by the Redux store and displayed in the UI
    }
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Card sx={{ width: '100%', overflow: 'visible' }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              pt: 4,
              pb: 2,
              bgcolor: 'primary.main',
              color: 'white',
              borderRadius: '4px 4px 0 0',
            }}
          >
            <LockOutlined sx={{ fontSize: 40, mb: 1 }} />
            <Typography component="h1" variant="h4" fontWeight="bold">
              SQL DB LLM Agent
            </Typography>
          </Box>

          <CardContent sx={{ px: 4, py: 3 }}>
            <Typography component="h2" variant="h5" align="center" sx={{ mb: 3 }}>
              로그인
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} noValidate>
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="사용자명"
                name="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={e => setUsername(e.target.value)}
                error={!!formErrors.username}
                helperText={formErrors.username}
                disabled={loading}
                variant="outlined"
              />

              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="비밀번호"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                error={!!formErrors.password}
                helperText={formErrors.password}
                disabled={loading}
                variant="outlined"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleTogglePasswordVisibility}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2, py: 1.5, fontWeight: 'bold' }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : '로그인'}
              </Button>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ textAlign: 'center' }}>
                <Link
                  href="#"
                  variant="body2"
                  onClick={e => {
                    e.preventDefault();
                    alert('비밀번호 재설정을 위해 관리자에게 문의하세요');
                  }}
                >
                  비밀번호를 잊으셨나요?
                </Link>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 5 }}>
          © {new Date().getFullYear()} SQL DB LLM Agent System
        </Typography>
      </Box>
    </Container>
  );
};

export default Login;
