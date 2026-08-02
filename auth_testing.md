# HorizonQuest Auth Testing Playbook (Emergent Google Auth)

## Auth model
- Emergent Google OAuth. Session token stored in `db.user_sessions`, httpOnly cookie `session_token` (also accepts `Authorization: Bearer`).
- Users in `db.users` keyed by custom `user_id`. Roles: `explorer` | `guide` (null until chosen at /welcome).

## Create Test User & Session (mongosh)
```
mongosh --eval "
use('test_database');
var uid='test-explorer-'+Date.now();
var st='test_session_'+Date.now();
db.users.insertOne({user_id:uid, email:'exp.'+Date.now()+'@test.com', name:'Test Explorer', picture:'', role:'explorer', horizon_points:0, compass_marks:0, fleet:null, expedition_ids:[], created_at:new Date().toISOString()});
db.user_sessions.insertOne({user_id:uid, session_token:st, expires_at:new Date(Date.now()+7*24*3600*1000).toISOString(), created_at:new Date().toISOString()});
print('SESSION '+st); print('UID '+uid);
"
```
For a Guide, set role:'guide'.

## Backend API test
```
curl -s $URL/api/auth/me -H "Authorization: Bearer <session_token>"
curl -s -X POST $URL/api/expeditions -H "Authorization: Bearer <guide_token>" -H "Content-Type: application/json" -d '{"name":"QA Voyage"}'
curl -s -X POST $URL/api/expeditions/join -H "Authorization: Bearer <explorer_token>" -H "Content-Type: application/json" -d '{"join_code":"XXXXXX"}'
curl -s -X POST $URL/api/trials/t1-q1/submit -H "Authorization: Bearer <explorer_token>" -H "Content-Type: application/json" -d '{"answers":{"a":"Stores a value you can reuse","b":"8","c":"player_lives"},"reflection":"..."}'
curl -s "$URL/api/leaderboard" -H "Authorization: Bearer <explorer_token>"
```

## Browser cookie injection
```
await page.context.add_cookies([{ "name":"session_token","value":"<token>","domain":"<host>","path":"/","httpOnly":true,"secure":true,"sameSite":"None" }])
```
