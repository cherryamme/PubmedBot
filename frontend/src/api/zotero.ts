import client from './client';
import type { ZoteroAccount, ZoteroCollection } from '../types';

// Accounts
export async function getZoteroAccounts(): Promise<ZoteroAccount[]> {
  const { data } = await client.get('/zotero/accounts');
  return data;
}

export async function addZoteroAccount(body: { name: string; library_id: string; library_type: string; api_key: string }): Promise<ZoteroAccount> {
  const { data } = await client.post('/zotero/accounts', body);
  return data;
}

export async function deleteZoteroAccount(id: number): Promise<void> {
  await client.delete(`/zotero/accounts/${id}`);
}

// Collections
export async function getZoteroCollections(accountId: number): Promise<ZoteroCollection[]> {
  const { data } = await client.get(`/zotero/accounts/${accountId}/collections`);
  return data;
}

// Export
export async function exportToZotero(paperId: number, accountId: number, collectionKey?: string, includeChat = true) {
  const { data } = await client.post(`/papers/${paperId}/zotero/export`, {
    account_id: accountId,
    collection_key: collectionKey,
    include_chat: includeChat,
  });
  return data;
}
