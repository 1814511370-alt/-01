const n={viewer:1,operator:2,admin:3};function t(r,e){return e?r?(n[r]||0)>=(n[e]||0):!1:!0}function a(r){return t(r,"operator")}function i(r){return t(r,"admin")}export{a,i as c,t as h};
