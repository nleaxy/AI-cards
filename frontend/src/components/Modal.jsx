import React from 'react';
import { X, AlertTriangle } from 'lucide-react';

const Modal = ({ isOpen, onClose, onConfirm, title, message, confirmText = "Удалить", cancelText = "Отмена", danger = false }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          <X size={24} />
        </button>
        
        <div className="modal-header">
          {danger && <AlertTriangle size={48} className="modal-icon-danger" />}
          <h2>{title}</h2>
        </div>
        
        <div className="modal-body">
          <p>{message}</p>
        </div>
        
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            {cancelText}
          </button>
          <button 
            className={`btn ${danger ? 'btn-wrong' : 'btn-primary'}`}
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Modal;