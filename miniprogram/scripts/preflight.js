const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const project = require('../project.config.json');
const config = require('../config');
const errors = [];
let local = {};
const privatePath = path.join(root, 'project.private.config.json');
if (fs.existsSync(privatePath)) local = JSON.parse(fs.readFileSync(privatePath, 'utf8'));
const effectiveSettings = {...project.setting, ...local.setting};
if (!/^wx[0-9a-f]{16}$/.test(project.appid)) errors.push('需要真实独立 AppID');
if (effectiveSettings.urlCheck !== true) errors.push('正式版必须开启有效 urlCheck，含本机覆盖配置');
if (config.development !== false) errors.push('正式版必须显式关闭 development');
try {
  const url = new URL(config.baseURL);
  if (url.protocol !== 'https:' || url.username || url.password || ['localhost','127.0.0.1','[::1]'].includes(url.hostname) || url.hostname.endsWith('.local') || !url.hostname.includes('.')) throw Error();
} catch (_) { errors.push('需要有效的正式 HTTPS API 域名'); }
if (!config.privacyOperator || !config.privacyOperator.trim()) errors.push('需要真实隐私运营主体');
if (!config.privacyContact || !/(@|\+?\d[\d -]{6,})/.test(config.privacyContact)) errors.push('需要真实隐私联系邮箱或电话');
if (errors.length) { console.error(errors.join('\n')); process.exit(1); }
console.log('配置静态检查通过；仍需合法域名、隐私审核和真机验收');
