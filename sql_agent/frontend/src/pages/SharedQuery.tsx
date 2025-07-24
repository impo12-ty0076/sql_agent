import React from 'react';
import { useLocation } from 'react-router-dom';
import SharedQueryView from '../components/history/SharedQueryView';

const SharedQuery: React.FC = () => {
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const shareId = queryParams.get('id') || '';
  const token = queryParams.get('token') || '';

  if (!shareId || !token) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <h2>잘못된 공유 링크</h2>
        <p>유효한 공유 ID와 토큰이 필요합니다.</p>
      </div>
    );
  }

  return <SharedQueryView shareId={shareId} token={token} />;
};

export default SharedQuery;
