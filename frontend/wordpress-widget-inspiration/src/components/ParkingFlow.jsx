import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import './ParkingFlow.css';

const API_BASE = '/api';

function ParkingFlow({ sessionId, onComplete, onCancel }) {
  const [step, setStep] = useState('slots');
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [holdExpiry, setHoldExpiry] = useState(null);
  const [patientData, setPatientData] = useState({
    name: '',
    phone: '',
    email: '',
    appointmentReferenceNumber: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    fetchSlots();
  }, [selectedDate]);

  useEffect(() => {
    if (holdExpiry) {
      const interval = setInterval(() => {
        const now = new Date();
        const expiry = new Date(holdExpiry);
        if (now >= expiry) {
          setError('Your hold has expired. Please select a new slot.');
          setSelectedSlot(null);
          setHoldExpiry(null);
          setStep('slots');
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [holdExpiry]);

  const fetchSlots = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/slots/parking`, {
        params: { date: selectedDate }
      });
      setSlots(response.data);
    } catch (err) {
      setError('Failed to load available parking slots');
    } finally {
      setLoading(false);
    }
  };

  const handleSlotSelect = async (slot) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE}/slots/parking/${slot.id}/hold`, {
        sessionId
      });
      // Store the sessionId from the server response (may be different if server created new one)
      const serverSessionId = response.data?.sessionId || sessionId;
      setSelectedSlot({
        ...slot,
        _sessionId: serverSessionId
      });
      setHoldExpiry(response.data.holdExpiry);
      setStep('details');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to hold parking slot');
      fetchSlots();
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Use the sessionId from the hold response if available, otherwise use the prop
      const actualSessionId = selectedSlot._sessionId || sessionId;
      
      console.log('Confirming parking reservation with:', {
        slotId: selectedSlot.id,
        sessionId: actualSessionId,
        storedSessionId: selectedSlot._sessionId,
        propSessionId: sessionId
      });
      
      const response = await axios.post(`${API_BASE}/reservations/parking`, {
        slotId: selectedSlot.id,
        patientData,
        sessionId: actualSessionId
      });
      onComplete(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to confirm parking reservation');
    } finally {
      setLoading(false);
    }
  };

  const formatTimeRemaining = () => {
    if (!holdExpiry) return '';
    const now = new Date();
    const expiry = new Date(holdExpiry);
    const diff = Math.max(0, Math.floor((expiry - now) / 1000));
    const mins = Math.floor(diff / 60);
    const secs = diff % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (step === 'slots') {
    return (
      <div className="parking-flow">
        <div className="parking-header">
          <h3>Reserve Parking</h3>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        <div className="parking-content">
          <div className="date-selector">
            <label>Select Date:</label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          {loading && <div className="loading">Loading parking slots...</div>}
          {!loading && slots.length === 0 && (
            <div className="empty-state">No available parking for this date.</div>
          )}
          {!loading && slots.length > 0 && (
            <div className="parking-grid">
              {slots.map((slot) => (
                <button
                  key={slot.id}
                  className="parking-card"
                  onClick={() => handleSlotSelect(slot)}
                  disabled={loading}
                >
                  <div className="spot-identifier">{slot.spot_identifier}</div>
                  <div className="zone-badge">{slot.zone}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (step === 'details') {
    return (
      <div className="parking-flow">
        <div className="parking-header">
          <h3>Complete Parking Reservation</h3>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        <div className="parking-content">
          {holdExpiry && (
            <div className="hold-timer">
              ⏱️ Hold expires in: {formatTimeRemaining()}
            </div>
          )}
          {selectedSlot && (
            <div className="selected-slot-info">
              <strong>Selected Spot:</strong> {selectedSlot.spot_identifier}
              <div>Zone: {selectedSlot.zone}</div>
              <div>Date: {format(new Date(selectedSlot.start_time), 'EEEE, MMMM d, yyyy')}</div>
            </div>
          )}
          <form onSubmit={handleSubmit} className="parking-form">
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                required
                value={patientData.name}
                onChange={(e) => setPatientData({ ...patientData, name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Phone Number *</label>
              <input
                type="tel"
                required
                value={patientData.phone}
                onChange={(e) => setPatientData({ ...patientData, phone: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Email *</label>
              <input
                type="email"
                required
                value={patientData.email}
                onChange={(e) => setPatientData({ ...patientData, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Appointment Reference Number</label>
              <input
                type="text"
                placeholder="Enter your appointment booking reference number"
                value={patientData.appointmentReferenceNumber}
                onChange={(e) => setPatientData({ ...patientData, appointmentReferenceNumber: e.target.value })}
              />
              <small className="form-hint">If you have an existing appointment, enter its reference number to link it with this parking reservation.</small>
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="form-actions">
              <button type="button" onClick={onCancel} className="btn-secondary">
                Cancel
              </button>
              <button type="submit" disabled={loading} className="btn-primary">
                {loading ? 'Confirming...' : 'Confirm Reservation'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return null;
}

export default ParkingFlow;

