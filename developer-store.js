export const REPOSITORY='c3xv05/NKNU-Campus-Simulator';
export const RECORD_MARKER='<!-- nknu-dev-record -->';
export const DRAFT_KEY='nknu-developer-drafts-v1';
export function readDrafts(storage){try{const data=JSON.parse(storage.getItem(DRAFT_KEY)||'[]');return Array.isArray(data)?data.filter(d=>d&&typeof d.id==='string'&&typeof d.title==='string'&&typeof d.body==='string'):[];}catch{return [];}}
export function recordBody(record){return `${RECORD_MARKER}\n<!-- local-id:${record.id.replace(/[^a-zA-Z0-9-]/g,'')} -->\n類型：${record.type==='report'?'問題回報':'開發者紀錄'}\n日期：${record.createdAt}\n\n${record.body}\n\n---\n位置／環境：\n\n\`\`\`json\n${JSON.stringify(record.context||{},null,2)}\n\`\`\`\n\n紀錄索引：#9`;}
export function issueLink(record){const prefix=record.type==='report'?'[問題回報]':'[開發者紀錄]';const url=new URL(`https://github.com/${REPOSITORY}/issues/new`);url.searchParams.set('title',prefix+' '+record.title);url.searchParams.set('body',recordBody(record));return url.href;}
export function cloudRecords(issues){return issues.filter(i=>!i.pull_request&&typeof i.body==='string'&&i.body.includes(RECORD_MARKER));}
