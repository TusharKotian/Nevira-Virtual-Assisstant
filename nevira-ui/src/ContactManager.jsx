import React, { useState, useEffect } from 'react';

const STORAGE_KEY = 'nevira_contacts_ui';

function loadContacts() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY) || '[]';
    return JSON.parse(raw);
  } catch (e) {
    return [];
  }
}

function saveContacts(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch (e) {}
}

export default function ContactManager({ onClose, onSelect }) {
  const [contacts, setContacts] = useState([]);
  const [editing, setEditing] = useState(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  useEffect(() => {
    setContacts(loadContacts());
  }, []);

  const startAdd = () => {
    setEditing(null);
    setName('');
    setEmail('');
  };

  const startEdit = (c) => {
    setEditing(c.id);
    setName(c.name);
    setEmail(c.email);
  };

  const save = () => {
    if (!name.trim() || !email.trim()) return;
    const next = contacts.slice();
    if (editing) {
      const idx = next.findIndex((x) => x.id === editing);
      if (idx >= 0) next[idx] = { ...next[idx], name: name.trim(), email: email.trim() };
    } else {
      next.push({ id: `c_${Date.now()}`, name: name.trim(), email: email.trim() });
    }
    setContacts(next);
    saveContacts(next);
    setName('');
    setEmail('');
    setEditing(null);
  };

  const remove = (id) => {
    const next = contacts.filter((c) => c.id !== id);
    setContacts(next);
    saveContacts(next);
  };

  const choose = (c) => {
    if (onSelect) onSelect(c);
    if (onClose) onClose();
  };

  return (
    <div className="email-popup-overlay">
      <div className="contact-manager">
        <div className="email-popup-header">
          <h3>📇 Contacts</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="contact-manager-body">
          <div className="contacts-list">
            {contacts.length === 0 && <div className="muted">No contacts yet — add one.</div>}
            {contacts.map((c) => (
              <div key={c.id} className="contact-row">
                <div className="contact-info">
                  <div className="contact-name">{c.name}</div>
                  <div className="contact-email">{c.email}</div>
                </div>
                <div className="contact-actions">
                  <button className="btn" onClick={() => choose(c)}>Select</button>
                  <button className="btn btn-secondary" onClick={() => startEdit(c)}>Edit</button>
                  <button className="btn btn-danger" onClick={() => remove(c.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>

          <div className="contact-editor">
            <h4>{editing ? 'Edit Contact' : 'Add Contact'}</h4>
            <div className="form-group">
              <label>Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@example.com" />
            </div>
            <div className="editor-actions">
              <button className="btn btn-primary" onClick={save}>{editing ? 'Save' : 'Add'}</button>
              <button className="btn btn-secondary" onClick={startAdd}>Clear</button>
            </div>
          </div>
        </div>
        <div className="email-popup-footer">
          <button className="btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
