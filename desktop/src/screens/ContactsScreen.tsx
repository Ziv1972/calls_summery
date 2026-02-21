/** Contacts screen - list, search, view calls per contact. */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import { formatDate } from "../utils/formatters";
import type { Contact, Call } from "../types/api";

export function ContactsScreen() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [search, setSearch] = useState("");
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [contactCalls, setContactCalls] = useState<Call[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadContacts();
  }, [search]);

  const loadContacts = async () => {
    try {
      const params: Record<string, unknown> = { page_size: 100 };
      if (search) params.q = search;
      const { data } = await apiClient.get("/contacts/", { params });
      setContacts(data.items);
    } catch {
      // Handled by client
    }
  };

  const selectContact = async (contact: Contact) => {
    setSelectedContact(contact);
    try {
      const { data } = await apiClient.get(`/contacts/${contact.id}/calls`);
      setContactCalls(data.items);
    } catch {
      setContactCalls([]);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-5">Contacts</h1>

      <div className="grid grid-cols-3 gap-6">
        {/* Contact list */}
        <div className="col-span-1 bg-white rounded-xl shadow-sm border">
          <div className="p-3 border-b">
            <input
              type="text"
              placeholder="Search contacts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="divide-y max-h-[70vh] overflow-y-auto">
            {contacts.length === 0 ? (
              <p className="p-4 text-sm text-slate-400">No contacts found</p>
            ) : (
              contacts.map((c) => (
                <div
                  key={c.id}
                  className={`p-3 cursor-pointer hover:bg-slate-50 ${selectedContact?.id === c.id ? "bg-blue-50" : ""}`}
                  onClick={() => selectContact(c)}
                >
                  <p className="text-sm font-medium">{c.name || "Unknown"}</p>
                  <p className="text-xs text-slate-500">{c.phone_number}</p>
                  {c.company && <p className="text-xs text-slate-400">{c.company}</p>}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Contact detail + calls */}
        <div className="col-span-2">
          {selectedContact ? (
            <div className="space-y-4">
              <div className="bg-white rounded-xl shadow-sm border p-5">
                <h2 className="text-lg font-semibold">{selectedContact.name || "Unknown"}</h2>
                <p className="text-sm text-slate-500">{selectedContact.phone_number}</p>
                {selectedContact.company && <p className="text-sm text-slate-400">{selectedContact.company}</p>}
                {selectedContact.email && <p className="text-sm text-slate-400">{selectedContact.email}</p>}
              </div>

              <div className="bg-white rounded-xl shadow-sm border p-5">
                <h3 className="font-semibold mb-3">Calls with {selectedContact.name || "this contact"}</h3>
                {contactCalls.length === 0 ? (
                  <p className="text-sm text-slate-400">No calls found</p>
                ) : (
                  <div className="space-y-2">
                    {contactCalls.map((call) => (
                      <div
                        key={call.id}
                        className="p-3 border rounded-lg hover:bg-slate-50 cursor-pointer"
                        onClick={() => navigate(`/calls/${call.id}`)}
                      >
                        <p className="text-sm font-medium">{call.original_filename}</p>
                        <p className="text-xs text-slate-500">{formatDate(call.created_at)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400">
              Select a contact to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
