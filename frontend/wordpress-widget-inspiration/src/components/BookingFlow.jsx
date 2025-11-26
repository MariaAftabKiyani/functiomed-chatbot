import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import './BookingFlow.css';

const API_BASE = '/api';

function BookingFlow({ sessionId, onSessionIdUpdate, onComplete, onCancel }) {
  const [step, setStep] = useState('welcome');
  const [slots, setSlots] = useState([]);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedTime, setSelectedTime] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [selectedService, setSelectedService] = useState(null);
  const [services, setServices] = useState([]);
  const [serviceSearchTerm, setServiceSearchTerm] = useState(''); // Add search functionality
  const [patientData, setPatientData] = useState({
    name: '',
    dob: '',
    phone: '',
    email: '',
    reason: '',
    insurance: ''
  });
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reservationId, setReservationId] = useState(null);

  const questions = [
    { key: 'name', label: 'What is your full name?', type: 'text', required: true },
    { key: 'dob', label: 'What is your date of birth? (YYYY-MM-DD)', type: 'date', required: true },
    { key: 'phone', label: 'What is your phone number?', type: 'tel', required: true },
    { key: 'email', label: 'What is your email address?', type: 'email', required: true },
    { key: 'reason', label: 'What is the reason for your visit?', type: 'textarea', required: false },
    { key: 'insurance', label: 'Do you have insurance details to provide? (Optional)', type: 'text', required: false }
  ];

  useEffect(() => {
    if (step === 'init' || step === 'selectService') {
      // Fetch services when booking flow starts or when selecting service
      fetchServices();
    }
    if (step === 'selectDate') {
      fetchSlots();
    }
  }, [step]);
  
  const fetchServices = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/services`);
      // Sort services alphabetically for better UX
      const sortedServices = (response.data || []).sort((a, b) => 
        a.name.localeCompare(b.name)
      );
      setServices(sortedServices);
      
      console.log(`Loaded ${sortedServices.length} services for booking`);
      
      // If still empty, set default services
      if (!response.data || response.data.length === 0) {
        setServices([
          { id: 'default_1', name: 'General Consultation' },
          { id: 'default_2', name: 'Physical Therapy' },
          { id: 'default_3', name: 'Physiotherapy' },
          { id: 'default_4', name: 'Infusion Therapy' },
          { id: 'default_5', name: 'Consultation' }
        ]);
      }
    } catch (err) {
      console.error('Failed to load services:', err);
      // Set default services on error
      setServices([
        { id: 'default_1', name: 'General Consultation' },
        { id: 'default_2', name: 'Physical Therapy' },
        { id: 'default_3', name: 'Physiotherapy' },
        { id: 'default_4', name: 'Infusion Therapy' },
        { id: 'default_5', name: 'Consultation' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchSlots = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedService) {
        params.service_type = selectedService;
      }
      const response = await axios.get(`${API_BASE}/slots/appointments`, { params });
      setSlots(response.data);
      
      // Extract unique dates from slots
      const dates = [...new Set(response.data.map(slot => {
        const date = new Date(slot.start_time);
        return date.toISOString().split('T')[0];
      }))].sort();
      setAvailableDates(dates);
    } catch (err) {
      setError('Failed to load available slots');
    } finally {
      setLoading(false);
    }
  };

  const getTimesForDate = (date) => {
    return slots
      .filter(slot => {
        const slotDate = new Date(slot.start_time);
        return slotDate.toISOString().split('T')[0] === date;
      })
      .map(slot => ({
        ...slot,
        time: format(new Date(slot.start_time), 'h:mm a')
      }))
      .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
  };

  const handleAnswer = () => {
    if (!inputValue.trim() && currentQuestion?.required) {
      setError('This field is required');
      return;
    }

    setPatientData({
      ...patientData,
      [currentQuestion.key]: inputValue
    });

    handleNextQuestion();
  };

  const handleNextQuestion = () => {
    const currentIndex = questions.findIndex(q => q.key === currentQuestion?.key);
    
    if (currentIndex < questions.length - 1) {
      const nextQuestion = questions[currentIndex + 1];
      setCurrentQuestion(nextQuestion);
      setInputValue(patientData[nextQuestion.key] || '');
      setError(null);
    } else {
      // All questions answered, proceed to service selection
      setStep('selectService');
      setCurrentQuestion(null);
    }
  };
  
  const handleServiceSelect = (service) => {
    setSelectedService(service);
    setStep('selectDate');
  };

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    setSelectedTime(null);
    setSelectedSlot(null);
    const times = getTimesForDate(date);
    if (times.length === 0) {
      setError('No available times for this date. Please select another date.');
      return;
    }
    setStep('selectTime');
  };

  const handleTimeSelect = async (slot) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE}/slots/appointments/${slot.id}/hold`, {
        sessionId
      });
      // Store the sessionId from the server response (may be different if server created new one)
      const serverSessionId = response.data?.sessionId || sessionId;
      setSelectedSlot({
        ...slot,
        _sessionId: serverSessionId
      });
      
      // Update parent's sessionId if server returned a new one
      if (response.data?.sessionId && response.data.sessionId !== sessionId && onSessionIdUpdate) {
        onSessionIdUpdate(response.data.sessionId);
      }
      setStep('confirm');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to hold slot. It may have been taken.');
      setStep('selectTime');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);

    try {
      // Use the sessionId from the hold response if available, otherwise use the prop
      const actualSessionId = selectedSlot._sessionId || sessionId;
      
      console.log('Confirming booking with:', {
        slotId: selectedSlot.id,
        sessionId: actualSessionId,
        storedSessionId: selectedSlot._sessionId,
        propSessionId: sessionId
      });
      
      const response = await axios.post(`${API_BASE}/reservations/appointments`, {
        slotId: selectedSlot.id,
        patientData,
        sessionId: actualSessionId
      });
      
      console.log('Booking response:', response.data);
      
      // Ensure we have the reservationId - check multiple possible fields
      const reservationId = response.data?.reservationId || 
                           response.data?.id || 
                           response.data?.reservation?.id ||
                           null;
      
      console.log('Reservation ID:', reservationId);
      
      // Update state in a way that ensures React sees the updates
      if (reservationId) {
        setReservationId(reservationId);
      }
      
      // Always show completion screen, even if reservationId is missing
      setStep('completed');
      setLoading(false);
      
      // Call onComplete with the full response data
      if (response.data) {
        const completeData = {
          ...response.data,
          reservationId: reservationId || response.data.reservationId || 'Pending'
        };
        console.log('Calling onComplete with:', completeData);
        onComplete(completeData);
      }
    } catch (err) {
      console.error('Booking confirmation error:', err);
      console.error('Error response:', err.response?.data);
      setError(err.response?.data?.error || err.message || 'Failed to confirm reservation');
      setLoading(false);
    }
  };

  // Welcome screen
  if (step === 'welcome' || step === 'init') {
    return (
      <div className="booking-flow">
        <div className="booking-header">
          <h3>Book an Appointment</h3>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        <div className="booking-content">
          <div className="welcome-message">
            <p>I'll help you book an appointment. Let me ask you a few questions to get started.</p>
          </div>
          <button 
            className="btn-primary" 
            onClick={() => {
              setStep('questions');
              setCurrentQuestion(questions[0]);
              setInputValue('');
            }}
          >
            Get Started
          </button>
        </div>
      </div>
    );
  }

  // Questions flow
  if (step === 'questions') {
    return (
      <div className="booking-flow">
        <div className="booking-header">
          <h3>Book an Appointment</h3>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        <div className="booking-content">
          <div className="question-section">
            <div className="question-progress">
              {questions.map((q, idx) => {
                const isAnswered = patientData[q.key];
                const isCurrent = q.key === currentQuestion?.key;
                return (
                  <div 
                    key={q.key}
                    className={`progress-dot ${isAnswered ? 'answered' : ''} ${isCurrent ? 'current' : ''}`}
                  />
                );
              })}
            </div>
            <div className="question-text">{currentQuestion?.label}</div>
            {error && <div className="error-message">{error}</div>}
            <div className="question-input">
              {currentQuestion?.type === 'textarea' ? (
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleAnswer();
                    }
                  }}
                  placeholder="Type your answer..."
                  rows="3"
                  autoFocus
                />
              ) : (
                <input
                  type={currentQuestion?.type || 'text'}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleAnswer();
                    }
                  }}
                  placeholder="Type your answer..."
                  autoFocus
                />
              )}
            </div>
            <div className="question-actions">
              <button type="button" onClick={onCancel} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleAnswer} className="btn-primary">
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Service selection step
  if (step === 'selectService') {
    // Filter services based on search term
    const filteredServices = services.filter(service =>
      service.name.toLowerCase().includes(serviceSearchTerm.toLowerCase())
    );
    
    return (
      <div className="booking-flow">
        <div className="booking-header">
          <h3>Select Service</h3>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        <div className="booking-content">
          {loading ? (
            <div className="loading">Loading services...</div>
          ) : services.length === 0 ? (
            <div className="error-message">No services available. Please try again later.</div>
          ) : (
            <>
              <p className="section-label">Please select a service ({services.length} available):</p>
              
              {/* Search bar for services */}
              {services.length > 10 && (
                <div className="service-search">
                  <input
                    type="text"
                    placeholder="Search services..."
                    value={serviceSearchTerm}
                    onChange={(e) => setServiceSearchTerm(e.target.value)}
                    className="service-search-input"
                  />
                  {serviceSearchTerm && (
                    <button 
                      className="service-search-clear"
                      onClick={() => setServiceSearchTerm('')}
                    >
                      ×
                    </button>
                  )}
                </div>
              )}
              
              {filteredServices.length === 0 ? (
                <div className="error-message">
                  No services found matching "{serviceSearchTerm}". Please try a different search term.
                </div>
              ) : (
                <div className="service-grid">
                  {filteredServices.map((service) => (
                    <button
                      key={service.id}
                      className={`service-card ${selectedService === service.name ? 'selected' : ''}`}
                      onClick={() => handleServiceSelect(service.name)}
                    >
                      <div className="service-name">{service.name}</div>
                    </button>
                  ))}
                </div>
              )}
              
              {serviceSearchTerm && filteredServices.length > 0 && (
                <p className="service-search-info">
                  Showing {filteredServices.length} of {services.length} services
                </p>
              )}
            </>
          )}
        </div>
      </div>
    );
  }

  // Date selection
  if (step === 'selectDate') {
    return (
      <div className="booking-flow">
        <div className="booking-header">
          <h3>Select a Date</h3>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        <div className="booking-content">
          {loading && <div className="loading">Loading available dates...</div>}
          {error && <div className="error-message">{error}</div>}
          {!loading && availableDates.length === 0 && (
            <div className="empty-state">No available dates found. Please try again later.</div>
          )}
          {!loading && availableDates.length > 0 && (
            <>
              <p className="section-prompt">When would you like to schedule your appointment?</p>
              <div className="dates-grid">
                {availableDates.map((date) => (
                  <button
                    key={date}
                    className={`date-card ${selectedDate === date ? 'selected' : ''}`}
                    onClick={() => handleDateSelect(date)}
                  >
                    <div className="date-day">{format(new Date(date), 'EEE')}</div>
                    <div className="date-number">{format(new Date(date), 'd')}</div>
                    <div className="date-month">{format(new Date(date), 'MMM')}</div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  // Time selection
  if (step === 'selectTime') {
    const times = getTimesForDate(selectedDate);
    return (
      <div className="booking-flow">
        <div className="booking-header">
          <h3>Select a Time</h3>
          <button className="close-btn" onClick={() => { setStep('selectDate'); setSelectedDate(null); }}>×</button>
        </div>
        <div className="booking-content">
          <p className="section-prompt">
            Available times for {format(new Date(selectedDate), 'EEEE, MMMM d, yyyy')}:
          </p>
          {error && <div className="error-message">{error}</div>}
          {loading && <div className="loading">Holding slot...</div>}
          <div className="times-grid">
            {times.map((slot) => (
              <button
                key={slot.id}
                className={`time-card ${selectedSlot?.id === slot.id ? 'selected' : ''}`}
                onClick={() => handleTimeSelect(slot)}
                disabled={loading}
              >
                <div className="time-text">{slot.time}</div>
                {slot.provider_name && (
                  <div className="time-info">{slot.provider_name}</div>
                )}
                {slot.service_type && (
                  <div className="time-info">{slot.service_type}</div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Confirmation
  if (step === 'confirm') {
    return (
      <div className="booking-flow">
        <div className="booking-header">
          <h3>Confirm Booking</h3>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        <div className="booking-content">
          <div className="confirmation-summary">
            <h4>Please review your booking details:</h4>
            <div className="summary-item">
              <strong>Date & Time:</strong> {format(new Date(selectedSlot.start_time), 'EEEE, MMMM d, yyyy at h:mm a')}
            </div>
            {selectedSlot.provider_name && (
              <div className="summary-item">
                <strong>Provider:</strong> {selectedSlot.provider_name}
              </div>
            )}
            {selectedSlot.service_type && (
              <div className="summary-item">
                <strong>Service:</strong> {selectedSlot.service_type}
              </div>
            )}
            <div className="summary-item">
              <strong>Name:</strong> {patientData.name}
            </div>
            <div className="summary-item">
              <strong>Date of Birth:</strong> {patientData.dob}
            </div>
            <div className="summary-item">
              <strong>Phone:</strong> {patientData.phone}
            </div>
            <div className="summary-item">
              <strong>Email:</strong> {patientData.email}
            </div>
            {patientData.reason && (
              <div className="summary-item">
                <strong>Reason:</strong> {patientData.reason}
              </div>
            )}
            {patientData.insurance && (
              <div className="summary-item">
                <strong>Insurance:</strong> {patientData.insurance}
              </div>
            )}
          </div>
          {error && <div className="error-message">{error}</div>}
          <div className="form-actions">
            <button type="button" onClick={() => setStep('selectDate')} className="btn-secondary">
              Back
            </button>
            <button onClick={handleConfirm} disabled={loading} className="btn-primary">
              {loading ? 'Confirming...' : 'Confirm Booking'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Completed
  if (step === 'completed') {
    return (
      <div className="booking-flow">
        <div className="booking-header">
          <h3>Booking Confirmed!</h3>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        <div className="booking-content">
          <div className="success-message">
            <div className="success-icon">✅</div>
            <h4>Your appointment has been confirmed!</h4>
            <div className="reference-number">
              <strong>Reference Number:</strong>
              <div className="ref-code">{reservationId || 'Generating...'}</div>
            </div>
            <div className="confirmation-details">
              {selectedSlot && (
                <p><strong>Date & Time:</strong> {format(new Date(selectedSlot.start_time), 'EEEE, MMMM d, yyyy at h:mm a')}</p>
              )}
              {patientData.name && (
                <p><strong>Patient:</strong> {patientData.name}</p>
              )}
              {patientData.email && (
                <p>A confirmation email will be sent to {patientData.email}</p>
              )}
            </div>
            <button onClick={onCancel} className="btn-primary" style={{ marginTop: '1rem' }}>
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default BookingFlow;
