(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push(["chunks/[root-of-the-server]__c2f6a0d8._.js",
"[externals]/node:buffer [external] (node:buffer, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("node:buffer", () => require("node:buffer"));

module.exports = mod;
}),
"[externals]/node:async_hooks [external] (node:async_hooks, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("node:async_hooks", () => require("node:async_hooks"));

module.exports = mod;
}),
"[project]/app/src/i18n/config.ts [middleware-edge] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "defaultLocale",
    ()=>defaultLocale,
    "locales",
    ()=>locales
]);
const locales = [
    'zh',
    'en'
];
const defaultLocale = 'zh';
}),
"[project]/app/messages/en.json (json)", ((__turbopack_context__) => {

__turbopack_context__.v({"common":{"loading":"Loading...","error":"An error occurred","save":"Save","cancel":"Cancel","delete":"Delete","edit":"Edit","confirm":"Confirm","back":"Back"},"auth":{"loginSuccess":"Login successful","loginFailed":"Login failed","registerSuccess":"Registration successful","registerFailed":"Registration failed"},"nav":{"dashboard":"Home","vault":"Resume","jobs":"Jobs","interview":"Interview","analytics":"Analytics","settings":"Me"},"dashboard":{"welcome":"Welcome back"},"vault":{"title":"Career Vault","description":"Manage your resume and experience data","empty":{"title":"No resume data","description":"Upload your resume and we'll parse it automatically"}},"jobs":{"title":"Applications","empty":"No applications yet"}});}),
"[project]/app/messages/zh.json (json)", ((__turbopack_context__) => {

__turbopack_context__.v({"common":{"loading":"加载中...","error":"发生错误","save":"保存","cancel":"取消","delete":"删除","edit":"编辑","confirm":"确认","back":"返回"},"auth":{"loginSuccess":"登录成功","loginFailed":"登录失败","registerSuccess":"注册成功","registerFailed":"注册失败"},"nav":{"dashboard":"首页","vault":"简历","jobs":"求职","interview":"面试准备","analytics":"数据","settings":"我的"},"dashboard":{"welcome":"欢迎回来"},"vault":{"title":"经历总库","description":"管理您的简历和经历数据","empty":{"title":"暂无简历数据","description":"上传简历，系统将自动解析并结构化"}},"jobs":{"title":"求职","empty":"暂无投递记录","add":"添加投递","company":"公司名称","position":"职位名称","link":"招聘链接","salary":"薪资范围","channel":"投递渠道","note":"备注","status":{"applied":"投递中","interview":"面试中","offer":"已offer","rejected":"已拒绝","closed":"已结束"}},"profile":{"title":"个人资料","name":"姓名","title_label":"职位","email":"邮箱","phone":"电话","bio":"个人简介","edit":"编辑资料","save":"保存"},"notifications":{"title":"消息通知","all":"全部","business":"业务","system":"系统","markAllRead":"全部已读","empty":"暂无消息"},"settings":{"title":"我的","profile":"个人资料","notifications":"消息通知","security":"账号安全","help":"帮助与反馈","logout":"退出登录"}});}),
"[project]/app/src/i18n/request.ts [middleware-edge] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>__TURBOPACK__default__export__
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2d$intl$2f$dist$2f$esm$2f$development$2f$server$2f$react$2d$server$2f$getRequestConfig$2e$js__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__$3c$export__default__as__getRequestConfig$3e$__ = __turbopack_context__.i("[project]/node_modules/next-intl/dist/esm/development/server/react-server/getRequestConfig.js [middleware-edge] (ecmascript) <export default as getRequestConfig>");
var __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$src$2f$i18n$2f$config$2e$ts__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/app/src/i18n/config.ts [middleware-edge] (ecmascript)");
;
;
const __TURBOPACK__default__export__ = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2d$intl$2f$dist$2f$esm$2f$development$2f$server$2f$react$2d$server$2f$getRequestConfig$2e$js__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__$3c$export__default__as__getRequestConfig$3e$__["getRequestConfig"])(async ({ requestLocale })=>{
    let locale = await requestLocale;
    if (!locale || ![
        'zh',
        'en'
    ].includes(locale)) {
        locale = __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$src$2f$i18n$2f$config$2e$ts__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__["defaultLocale"];
    }
    return {
        locale,
        messages: (await __turbopack_context__.f({
            "../../messages/en.json": {
                id: ()=>"[project]/app/messages/en.json (json)",
                module: ()=>Promise.resolve().then(()=>__turbopack_context__.i("[project]/app/messages/en.json (json)"))
            },
            "../../messages/zh.json": {
                id: ()=>"[project]/app/messages/zh.json (json)",
                module: ()=>Promise.resolve().then(()=>__turbopack_context__.i("[project]/app/messages/zh.json (json)"))
            }
        }).import(`../../messages/${locale}.json`)).default
    };
});
}),
"[project]/app/src/i18n/routing.ts [middleware-edge] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Link",
    ()=>Link,
    "redirect",
    ()=>redirect,
    "routing",
    ()=>routing,
    "usePathname",
    ()=>usePathname,
    "useRouter",
    ()=>useRouter
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2d$intl$2f$dist$2f$esm$2f$development$2f$routing$2f$defineRouting$2e$js__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__$3c$export__default__as__defineRouting$3e$__ = __turbopack_context__.i("[project]/node_modules/next-intl/dist/esm/development/routing/defineRouting.js [middleware-edge] (ecmascript) <export default as defineRouting>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2d$intl$2f$dist$2f$esm$2f$development$2f$navigation$2f$react$2d$server$2f$createNavigation$2e$js__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__$3c$export__default__as__createNavigation$3e$__ = __turbopack_context__.i("[project]/node_modules/next-intl/dist/esm/development/navigation/react-server/createNavigation.js [middleware-edge] (ecmascript) <export default as createNavigation>");
;
;
const routing = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2d$intl$2f$dist$2f$esm$2f$development$2f$routing$2f$defineRouting$2e$js__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__$3c$export__default__as__defineRouting$3e$__["defineRouting"])({
    locales: [
        'zh',
        'en'
    ],
    defaultLocale: 'zh'
});
const { Link, redirect, usePathname, useRouter } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2d$intl$2f$dist$2f$esm$2f$development$2f$navigation$2f$react$2d$server$2f$createNavigation$2e$js__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__$3c$export__default__as__createNavigation$3e$__["createNavigation"])(routing);
}),
"[project]/app/middleware.ts [middleware-edge] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "config",
    ()=>config,
    "default",
    ()=>__TURBOPACK__default__export__
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2d$intl$2f$dist$2f$esm$2f$development$2f$middleware$2f$middleware$2e$js__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next-intl/dist/esm/development/middleware/middleware.js [middleware-edge] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$src$2f$i18n$2f$routing$2e$ts__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/app/src/i18n/routing.ts [middleware-edge] (ecmascript)");
;
;
const __TURBOPACK__default__export__ = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2d$intl$2f$dist$2f$esm$2f$development$2f$middleware$2f$middleware$2e$js__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__["default"])(__TURBOPACK__imported__module__$5b$project$5d2f$app$2f$src$2f$i18n$2f$routing$2e$ts__$5b$middleware$2d$edge$5d$__$28$ecmascript$29$__["routing"]);
const config = {
    // Matcher entries need to be relative paths and have the same structure.
    // 使用更宽泛的 matcher 确保 /login 和 /register 被捕获
    matcher: [
        '/',
        '/(zh|en)/:path*',
        '/login',
        '/register',
        '/((?!api|_next|.*\\..*).*)'
    ]
};
}),
]);

//# sourceMappingURL=%5Broot-of-the-server%5D__c2f6a0d8._.js.map