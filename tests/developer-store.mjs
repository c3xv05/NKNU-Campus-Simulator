import assert from 'node:assert/strict';import {DRAFT_KEY,RECORD_MARKER,readDrafts,recordBody,issueLink,cloudRecords} from '../developer-store.js';
const record={id:'abc-123',type:'report',title:'校門 & 標線 #1',body:'花圃旁路面\n<測試> ? & #',createdAt:'2026-11-10T00:00:00Z',context:{position:{x:-275.3,y:0,z:525.8}}};
assert.deepEqual(readDrafts({getItem:()=>'{bad'}),[]);assert.deepEqual(readDrafts({getItem:()=>JSON.stringify([null])}),[]);
const storage={getItem:key=>key===DRAFT_KEY?JSON.stringify([record]):null};assert.equal(readDrafts(storage)[0].title,record.title);
const url=new URL(issueLink(record));assert.equal(url.origin,'https://github.com');assert.equal(url.searchParams.get('title'),'[問題回報] '+record.title);assert.equal(url.searchParams.get('body'),recordBody(record));assert(recordBody(record).includes(RECORD_MARKER));assert(recordBody(record).includes('local-id:abc-123'));assert(recordBody(record).includes('position'));
assert.equal(cloudRecords([{number:1,body:RECORD_MARKER},{number:2,body:'other'},{number:3,body:RECORD_MARKER,pull_request:{}}]).length,1);
console.log('PASS: durable draft parsing, record marker, exact encoded GitHub handoff, position metadata and PR exclusion');
