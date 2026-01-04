import React, { useState, useEffect } from 'react';
import { Container, Card, Table, Navbar, Button, Badge } from 'react-bootstrap';
import axios from 'axios';
import FloatingChatbot from './FloatingChatbot';
import './DashboardPage.css';

function DashboardPage({ sessionId, user, onLogout }) {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (sessionId) {
      loadPolicies();
    }
  }, [sessionId]);

  const loadPolicies = async () => {
    if (!sessionId) {
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.get('http://localhost:8000/policies', {
        params: { sessionId }
      });
      
      if (response.data && Array.isArray(response.data.policies)) {
        setPolicies(response.data.policies);
      } else {
        setPolicies([]);
      }
    } catch (err) {
      setPolicies([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'Active') {
      return <Badge bg="success">{status}</Badge>;
    }
    return <Badge bg="secondary">{status}</Badge>;
  };

  return (
    <div className="dashboard-container">
      <Navbar bg="white" variant="light" className="shadow-sm border-bottom">
        <Container fluid>
          <Navbar.Brand className="fw-bold text-primary">
            <i className="bi bi-shield-check me-2"></i>
            Insurance Portal
          </Navbar.Brand>
          <Navbar.Collapse className="justify-content-end">
            <Navbar.Text className="me-3">
              Welcome, <strong>{user?.name}</strong>
            </Navbar.Text>
            <Button variant="outline-secondary" size="sm" onClick={onLogout}>
              <i className="bi bi-box-arrow-right me-1"></i>
              Logout
            </Button>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <Container fluid className="py-4">
        <div className="mb-4">
          <h2 className="text-dark mb-2">My Policies</h2>
          <p className="text-muted">Manage and view your insurance policies</p>
        </div>

        {loading ? (
          <Card>
            <Card.Body className="text-center py-5">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </Card.Body>
          </Card>
        ) : policies.length === 0 ? (
          <Card>
            <Card.Body className="text-center py-5">
              <i className="bi bi-inbox" style={{ fontSize: '3rem', color: '#ccc' }}></i>
              <p className="text-muted mt-3">No policies found</p>
            </Card.Body>
          </Card>
        ) : (
          <Card className="shadow-sm">
            <Card.Body className="p-0">
              <Table hover className="mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Policy Number</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Coverage</th>
                    <th>Premium</th>
                    <th>Expiry Date</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((policy, idx) => (
                    <tr key={idx}>
                      <td>
                        <strong className="text-primary">{policy.policyNumber || 'N/A'}</strong>
                      </td>
                      <td>{policy.type || 'N/A'}</td>
                      <td>{getStatusBadge(policy.status || 'Unknown')}</td>
                      <td>{policy.coverage || 'N/A'}</td>
                      <td>{policy.premium || 'N/A'}</td>
                      <td>{policy.expiryDate || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        )}
      </Container>

      <FloatingChatbot sessionId={sessionId} user={user} />
    </div>
  );
}

export default DashboardPage;

