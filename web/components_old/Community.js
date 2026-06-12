Community={template:`<div>
<div class="flex items-center gap-2 mb-6">
<button @click="tab='feed'" :class="tab==='feed'?'btn btn-primary':'btn btn-ghost'" class="text-sm"><i class="fa-solid fa-image"></i> 图文广场</button>
<button @click="tab='video'" :class="tab==='video'?'btn btn-primary':'btn btn-ghost'" class="text-sm"><i class="fa-brands fa-tiktok"></i> 短视频</button>
<button @click="refreshFeed" class="btn btn-ghost text-sm"><i class="fa-solid fa-rotate"></i> 刷新</button>
<button @click="showCreate=true" class="btn btn-primary ml-auto text-sm"><i class="fa-solid fa-plus"></i> 发布</button>
</div>

<div v-if="tab==='feed'" class="space-y-6">
<div class="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4" v-if="posts.length>0">
<div v-for="post in posts" :key="post.id" class="break-inside-avoid card overflow-hidden cursor-pointer hover:shadow-xl transition-all duration-300 group" @click="openPost(post)">
<div class="relative overflow-hidden">
<img v-if="post.image_url" :src="post.image_url" class="w-full object-cover group-hover:scale-105 transition-transform duration-500" style="min-height:120px;max-height:320px"/>
<div v-else class="w-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-4xl" style="min-height:160px"><i class="fa-solid fa-image"></i></div>
<div class="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/60 to-transparent pointer-events-none"></div>
<p class="absolute bottom-3 left-3 right-3 text-white font-bold text-sm line-clamp-2 leading-snug drop-shadow-lg">{{post.title}}</p>
</div>
<div class="p-3 flex items-center justify-between">
<div class="flex items-center gap-2">
<div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-400 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">{{(post.author||{}).username?post.author.username[0]:'U'}}</div>
<span class="text-xs text-gray-500 dark:text-gray-400">{{(post.author||{}).username||'匿名用户'}}</span>
</div>
<div class="flex items-center gap-3 text-xs text-gray-400">
<span class="flex items-center gap-1 cursor-pointer hover:text-red-500 transition-colors" @click.stop="likePost(post)"><i :class="post.liked?'fa-solid fa-heart text-red-500':'fa-regular fa-heart'"></i> {{post.likes||0}}</span>
</div>
</div>
</div>
</div>
<div class="text-center py-6" v-if="posts.length>0"><button @click="loadMorePosts" class="btn btn-ghost text-sm"><i class="fa-solid fa-arrow-down mr-1"></i> 加载更多</button></div>
<div v-else class="text-center py-20"><i class="fa-solid fa-camera-retro text-6xl text-gray-300 dark:text-gray-600 mb-4 block"></i><p class="text-gray-400 text-lg">还没有笔记，快来发布第一篇吧</p><button @click="showCreate=true" class="btn btn-primary mt-4"><i class="fa-solid fa-pen"></i> 发布笔记</button></div>

<div v-if="selectedPost" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="selectedPost=null">
<div class="card max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto animate-fadeIn">
<button @click="selectedPost=null" class="float-right p-2 text-gray-400 hover:text-gray-600"><i class="fa-solid fa-xmark text-xl"></i></button>
<img v-if="selectedPost.image_url" :src="selectedPost.image_url" class="w-full max-h-[400px] object-cover rounded-xl mt-6"/>
<h2 class="text-xl font-bold mt-4">{{selectedPost.title}}</h2>
<p class="text-gray-600 dark:text-gray-300 mt-2 leading-relaxed whitespace-pre-line">{{selectedPost.content}}</p>
<div class="flex items-center gap-3 mt-4 pt-4 border-t border-gray-200 dark:border-slate-700">
<div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-cyan-500 flex items-center justify-center text-white font-bold">{{(selectedPost.author||{}).username?selectedPost.author.username[0]:'U'}}</div>
<div><p class="font-medium text-sm">{{(selectedPost.author||{}).username||'匿名用户'}}</p><p class="text-xs text-gray-400">{{formatTime(selectedPost.created_at)}}</p></div>
<button @click="likePost(selectedPost)" class="ml-auto flex items-center gap-1 btn btn-ghost text-sm"><i :class="selectedPost.liked?'fa-solid fa-heart text-red-500':'fa-regular fa-heart'"></i> {{selectedPost.likes||0}}</button>
</div>
</div>
</div>
</div>

<div v-if="tab==='video'" class="relative max-w-md mx-auto" style="height:calc(100vh - 180px)">
<div v-if="videoPosts.length===0" class="h-full flex flex-col items-center justify-center text-center"><i class="fa-brands fa-tiktok text-6xl text-gray-300 dark:text-gray-600 mb-4 block"></i><p class="text-gray-400 text-lg">还没有短视频，快来发布吧</p><button @click="showCreate=true" class="btn btn-primary mt-4"><i class="fa-solid fa-video"></i> 发布视频</button></div>
<div v-else class="h-full overflow-y-scroll snap-y snap-mandatory scroll-smooth rounded-2xl" ref="videoFeed" @scroll="onVideoScroll">
<div v-for="(post,idx) in videoPosts" :key="post.id" class="snap-start snap-always h-full relative bg-black flex items-center justify-center">
<video v-if="post.video_url" :ref="el=>setVideoRef(el,idx)" :src="post.video_url" class="w-full h-full object-cover" loop playsinline muted @click="togglePlay(idx)" @loadeddata="onVideoLoaded(idx)"></video>
<div v-else class="w-full h-full bg-gradient-to-b from-gray-800 to-gray-900 flex items-center justify-center text-white/50"><i class="fa-solid fa-video-slash text-5xl"></i></div>
<div class="absolute right-4 bottom-24 flex flex-col items-center gap-6 z-10">
<button @click="likePost(post)" class="flex flex-col items-center text-white"><div class="w-12 h-12 rounded-full bg-white/10 backdrop-blur flex items-center justify-center text-xl hover:bg-white/20 transition-all" :class="post.liked?'text-red-500':''"><i :class="post.liked?'fa-solid fa-heart':'fa-regular fa-heart'"></i></div><span class="text-xs mt-1 font-medium">{{post.likes||0}}</span></button>
<button class="flex flex-col items-center text-white"><div class="w-12 h-12 rounded-full bg-white/10 backdrop-blur flex items-center justify-center text-lg hover:bg-white/20 transition-all"><i class="fa-regular fa-comment"></i></div><span class="text-xs mt-1">0</span></button>
<button class="flex flex-col items-center text-white"><div class="w-12 h-12 rounded-full bg-white/10 backdrop-blur flex items-center justify-center text-lg hover:bg-white/20 transition-all"><i class="fa-solid fa-share"></i></div><span class="text-xs mt-1">分享</span></button>
</div>
<div class="absolute left-4 right-16 bottom-6 z-10 text-white">
<div class="flex items-center gap-2 mb-2"><div class="w-9 h-9 rounded-full bg-gradient-to-br from-pink-400 to-red-500 flex items-center justify-center text-white font-bold text-sm">{{(post.author||{}).username?post.author.username[0]:'U'}}</div><span class="font-semibold text-sm">{{(post.author||{}).username||'匿名用户'}}</span><button class="ml-2 px-4 py-1 rounded-full border border-white/60 text-xs font-medium hover:bg-white/20 transition-all">关注</button></div>
<p class="text-sm leading-relaxed line-clamp-2">{{post.title}}</p>
<div v-if="post.content" class="mt-1 text-xs text-white/70 line-clamp-2">{{post.content}}</div>
</div>
<div v-if="post.playing===false" class="absolute inset-0 flex items-center justify-center pointer-events-none"><div class="w-20 h-20 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white text-3xl"><i class="fa-solid fa-play ml-1"></i></div></div>
</div>
</div>
<div class="absolute bottom-2 left-0 right-0 text-center z-20" v-if="videoPosts.length>0"><button @click="loadMoreVideos" class="text-white/60 hover:text-white text-xs bg-black/30 rounded-full px-4 py-1.5 backdrop-blur"><i class="fa-solid fa-rotate mr-1"></i>换一批</button></div>
</div>

<div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="showCreate=false">
<div class="card max-w-lg w-full mx-4 p-6 animate-fadeIn max-h-[90vh] overflow-y-auto">
<div class="flex items-center justify-between mb-4"><h3 class="text-lg font-bold"><i class="fa-solid fa-pen-to-square mr-2 text-blue-500"></i>发布新内容</h3><button @click="showCreate=false" class="text-gray-400 hover:text-gray-600 text-xl"><i class="fa-solid fa-xmark"></i></button></div>
<div class="flex gap-3 mb-4"><button @click="createType='image'" :class="createType==='image'?'btn btn-primary':'btn btn-ghost'" class="flex-1 justify-center text-sm"><i class="fa-solid fa-image"></i> 图文笔记</button><button @click="createType='video'" :class="createType==='video'?'btn btn-primary':'btn btn-ghost'" class="flex-1 justify-center text-sm"><i class="fa-solid fa-video"></i> 短视频</button></div>
<form @submit.prevent="createPost" class="space-y-4">
<div><label class="text-sm font-medium text-gray-600 dark:text-gray-400 block mb-1">标题</label><input v-model="newPost.title" class="input" required placeholder="给你的内容起个标题..."/></div>
<div><label class="text-sm font-medium text-gray-600 dark:text-gray-400 block mb-1">正文</label><textarea v-model="newPost.content" class="input" rows="4" placeholder="分享你的维修经验、检测心得..."></textarea></div>
<div><label class="text-sm font-medium text-gray-600 dark:text-gray-400 block mb-1">{{createType==='image'?'上传图片':'上传视频'}}</label><input type="file" :accept="createType==='image'?'image/*':'video/*'" @change="onMediaSelect" ref="mediaInput" class="hidden"/><div v-if="!mediaPreview" @click="$refs.mediaInput.click()" class="border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 transition-colors"><i class="fa-solid fa-cloud-arrow-up text-3xl text-gray-400 mb-2 block"></i><p class="text-sm text-gray-500">{{createType==='image'?'点击上传图片':'点击上传视频'}}</p></div><div v-else class="relative"><img v-if="createType==='image'" :src="mediaPreview" class="rounded-xl max-h-48 object-cover w-full"/><video v-else :src="mediaPreview" controls class="rounded-xl max-h-48 w-full"></video><button type="button" @click="clearMedia" class="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/50 text-white flex items-center justify-center"><i class="fa-solid fa-xmark text-sm"></i></button></div></div>
<button type="submit" :disabled="creating" class="btn btn-primary w-full justify-center"><i :class="creating?'fa-solid fa-spinner fa-spin':'fa-solid fa-paper-plane'"></i> {{creating?'发布中...':'立即发布'}}</button>
</form>
</div>
</div>
</div>`,
data(){const now=Date.now();const h=(h)=>new Date(now-h*3600000).toISOString();const img=(s)=>'https://picsum.photos/seed/'+s+'/400/500';const V='/web/videos/';return{tab:'feed',postSeed:0,videoSeed:0,posts:[
{id:1,title:'自己动手修复车门划痕，3M抛光蜡省了500块！',content:"上个月车门被电动车剐了一道，4S店报价600还要等三天。买了3M抛光蜡35块加掌上抛光机89块，总共不到125块搞定！\n\n步骤：1.先判断划痕深度 2.洗车泥去污 3.抛光蜡挤抛光盘上1500转低速研磨 4.沿划痕方向单向往复不要画圈 5.上封体蜡收光。\n\n效果基本看不出来，4S店朋友说这水平可以接活了。",image_url:img('car-polish'),likes:1283,liked:false,author:{username:'修车达人阿杰'},created_at:h(3)},
{id:2,title:'补漆笔到底是不是智商税？实测6款热门产品',content:"从拼多多9.9到淘宝68块，买了6款销量最高的补漆笔实测。结论：补漆笔不是智商税但90%的人用错了。\n\n正确用法：1.酒精棉片彻底脱脂 2.薄涂5-8层每层间隔30分钟 3.静置24小时 4.2000目至3000目水砂纸打磨 5.抛光机加细蜡收光。\n\n点缤色差最小，车仆性价比高，3M附着力最好。补漆笔适合小面积点状破损，大面积还是去专业店。",image_url:img('paint-pen'),likes:896,liked:false,author:{username:'汽车养护师老王'},created_at:h(8)},
{id:3,title:'无腻子修复是骗局吗？28年老师傅说句实话',content:"最近抖音上无腻子修复和数据复原火得不行。\n\n传统钣金：拉出形状刮腻子填平打磨喷漆。\n无腻子：专用工具从背面逐点顶出配合热收火技术恢复原始数据。\n\n优点：腻子层会老化开裂无腻子从根源解决，保留更多原厂电泳层。\n局限：死褶撕裂很难完全无腻子，对师傅手艺要求极高，价格1.5到2倍。\n辨别：漆膜仪测厚度，原厂80到150微米，超200微米就是上了腻子。",image_url:img('dent-tools'),likes:2456,liked:false,author:{username:'钣金老孙头'},created_at:h(14)},
{id:4,title:'AI视觉检测钢缺陷，产线实测98.7%准确率',content:"厂里去年上了AI视觉检测系统检测热轧钢板表面缺陷，运行半年多。\n\n实际指标：缺陷检出率98.7%，误报率2.1%，单帧推理18ms，支持11种缺陷类型，稳定运行4300多小时。\n\n技术栈：改进YOLOv10n加4K线扫相机加多光谱环形光源。\n\n踩坑：LED环形光下夹杂物和氧化皮太像换多光谱才拉开，公开数据集NEU上线召回率仅72%补了3个月产线样本才到98%加。\n\n总结：打光样本环境控制比模型本身重要得多。",image_url:img('steel-inspect'),likes:1567,liked:false,author:{username:'工业视觉工程师老周'},created_at:h(20)},
{id:5,title:'凹陷无痕修复全程记录：保留原车漆太香了',content:"冰雹砸了引擎盖大大小小7个坑。\n\n师傅先用强光灯找凹陷边界看了半小时，热风枪加热到60度，从引擎盖内侧用撬棒逐点顶出，最大的坑修了2小时。\n\n从早上10点到下午5点7个坑全部修复。费用800块，4S店报价2800。效果：保留了原厂漆强光下也看不出来！\n\n提醒：凹陷修复仅适用于漆面无破损情况，铝件比钢难修。",image_url:img('dent-repair'),likes:978,liked:false,author:{username:'爱车如命的阿涛'},created_at:h(26)},
{id:6,title:'牙膏修复划痕实测！零成本到底管不管用？',content:"网上说用牙膏能去划痕实测3道不同深度划痕。\n\nA道发丝划痕：有效来回擦3次基本消失。\nB道中度划痕：变淡约30%没法完全消除。\nC道深度划痕：完全无效已伤到色漆层。\n\n结论：牙膏大法仅适用于最轻微发丝划痕清漆层，要用纯白色牙膏擦拭方向一致不要画圈。",image_url:img('toothpaste'),likes:2103,liked:false,author:{username:'撸车师兄'},created_at:h(32)},
{id:7,title:'老车翻新整备：凯迪拉克XT5底盘除锈加鹦鹉漆',content:"收了一台2017年XT5，12万公里底盘锈得不成样子花了整一个月翻新。\n\n底盘：喷砂加角磨机除锈3天，环氧底漆加底盘装甲胶，更换全车胶套减震器。\n漆面：全车打磨至裸铁加环氧底漆加中途底漆加鹦鹉923-255清漆，每层水磨800至2000目，最后3道抛光。\n\n翻新后漆面比新车还亮！",image_url:img('car-restore'),likes:3456,liked:false,author:{username:'鹏德钣喷-老车翻新'},created_at:h(38)},
{id:8,title:'从传统图像处理到深度学习：工业缺陷检测技术选型指南',content:"做工业视觉检测5年从Halcon到PyTorch。\n\n传统方法：尺寸测量定位计数更快更准，缺陷标准明确场景，产线稳定环境。\n深度学习：缺陷形态多变长尾场景，纹理背景复杂表面，语义理解任务。\n\n混合架构是工业界共识：传统做定位加测量，DL做缺陷检测加分类。\n推荐路线：Halcon基础到OpenCV实践到PyTorch加UNet到YOLO到TensorRT部署。",image_url:img('ai-industry'),likes:1892,liked:false,author:{username:'工业视觉老K'},created_at:h(45)},
{id:9,title:'汽车焊装质量检测：从人工目检到AI视觉的升级之路',content:"长安某车型焊装车间视觉检测升级实战。\n\n背景：焊装线60JPH，4个质检员目检疲劳后漏检率超8%。\n方案：8个工业相机加环形偏振光源加边缘服务器2乘RTX4080，YOLOv8n加传统算法。\n效果：检测5分钟变23秒效率提升92%，漏检8%变0.3%，8个月回本。\n\n系统稳定运行一年多每天检测约1200台车。",image_url:img('welding-ai'),likes:1432,liked:false,author:{username:'汽车智造工程师'},created_at:h(52)},
{id:10,title:'干货：车身漆面橘皮流挂颗粒缺陷速查手册',content:"常见漆面缺陷速查：\n\n1.橘皮：漆面像橘子皮凹凸，轻微抛光或水砂后重喷。\n2.流挂：泪痕状凸起，2000目水砂打磨加抛光。\n3.颗粒灰尘：凸起小颗粒，粘土布或水砂加抛光。\n4.鱼眼缩孔：圆形凹陷油污硅酮污染，必须打磨至底漆重喷。\n5.失光哑光：漆面无光泽，轻度抛光或重度重喷。\n\n养护：新车3月内不打蜡，洗车用中性液，鸟粪树胶快清理。",image_url:img('paint-defects'),likes:867,liked:false,author:{username:'漆面质检阿华'},created_at:h(60)}
],videoPosts:[
{id:101,title:'30秒学会划痕修复：3M抛光蜡大法',content:'#DIY修复 #汽车养护 #划痕修复',video_url:V+'01_scratch_repair.mp4',likes:10243,liked:false,playing:false,author:{username:'修车小李哥'},created_at:h(6)},
{id:102,title:'车间实拍：AI视觉检测钢缺陷全过程',content:'#AI视觉 #工业检测 #钢缺陷',video_url:V+'02_ai_inspection.mp4',likes:5234,liked:false,playing:false,author:{username:'工业视觉前线'},created_at:h(16)},
{id:103,title:'沉浸式老车翻新：从破烂到崭新极度解压',content:'#老车翻新 #钣金喷漆 #鹦鹉漆',video_url:V+'03_car_restoration.mp4',likes:18923,liked:false,playing:false,author:{username:'鹏德钣喷'},created_at:h(22)},
{id:104,title:'无腻子凹陷修复：数据复原技术全程演示',content:'#无腻子修复 #凹陷修复 #保留原车漆',video_url:V+'04_dent_repair.mp4',likes:7834,liked:false,playing:false,author:{username:'钣金老孙头'},created_at:h(30)},
{id:105,title:'汽车漆面精补：最小面积喷涂工艺',content:'#局部补漆 #漆面精补 #钣金喷漆',video_url:V+'05_paint_touchup.mp4',likes:4567,liked:false,playing:false,author:{username:'漆面大师阿文'},created_at:h(40)},
{id:106,title:'焊装产线AI质检：每秒检测3个焊点',content:'#汽车制造 #焊装检测 #AI质检',video_url:V+'06_welding_qa.mp4',likes:3156,liked:false,playing:false,author:{username:'汽车智造工程师'},created_at:h(50)}
],selectedPost:null,showCreate:false,createType:'image',newPost:{title:'',content:''},mediaFile:null,mediaPreview:null,creating:false,videoRefs:{},currentVideoIdx:0}},
methods:{async loadPosts(){},refreshFeed(){this.postSeed++;const s=this.postSeed;const now=Date.now();const h=(h)=>new Date(now-h*3600000).toISOString();const img=(seed)=>'https://picsum.photos/seed/'+seed+s+'/400/500';const fresh=[{id:now+1,title:'汽车凹陷修复工具实测：这3款撬棒最好用',image_url:img('dent-tools2'),likes:432+s*100,liked:false,author:{username:'凹陷修复小陈'},created_at:h(0.1),content:"做凹陷修复3年用过不下20款撬棒推荐3款。日本田岛弹性好不伤漆适合精细操作，德力西套装性价比高新手上路首选。提醒：工具重要但手艺更重要新手先拿废钣金练手！"},{id:now+2,title:'钣金喷漆行内黑话大全：新人避坑必看',image_url:img('slang-guide'),likes:678+s*50,liked:false,author:{username:'修车老司机'},created_at:h(0.2),content:"进修理厂听到这些词别懵！鹦鹉漆是高端清漆品牌不是真的鹦鹉。橘皮是漆面像橘子皮喷枪没调好。苍蝇屎是漆面小颗粒。咬底是新旧漆起反应起皱。收藏备用修车时显得你很懂行！"},{id:now+3,title:'工业相机选型指南：线扫vs面阵别再选错了',image_url:img('camera-guide'),likes:534+s*30,liked:false,author:{username:'工业视觉老K'},created_at:h(0.3),content:"工业视觉检测中相机选型直接影响检测效果。面阵相机一次拍摄整个画面适合静态检测。线扫相机逐行扫描拼接适合卷材板材连续检测。关键参数：分辨率等于缺陷最小尺寸除以3。"},{id:now+4,title:'汽车底盘装甲到底要不要做？修理厂不会说的实话',image_url:img('undercoat'),likes:891+s*40,liked:false,author:{username:'底盘专家老张'},created_at:h(0.4),content:"新车要不要做底盘装甲？建议做：沿海地区盐雾腐蚀、北方冬季融雪剂、经常跑烂路。不建议：城市通勤车原厂防腐足够、干燥地区、3年以上老车。价格参考：材料加工时800到1500。"},{id:now+5,title:'工业缺陷检测常用公开数据集横评：NEU到GC10',image_url:img('datasets'),likes:432+s*20,liked:false,author:{username:'工业视觉老周'},created_at:h(0.5),content:"整理了工业缺陷检测常用公开数据集。NEU-DET：6种热轧钢缺陷1800张入门首选。GC10-DET：10种钢缺陷3570张覆盖面更广。KolektorSDD：塑料表面缺陷小样本挑战。经验：公开数据集做预训练可以上线一定要用产线真实样本finetune。"}];this.posts=[...fresh,...this.posts]},loadMorePosts(){this.refreshFeed()},loadMoreVideos(){this.videoSeed++;const s=this.videoSeed;const now=Date.now();const h=(h)=>new Date(now-h*3600000).toISOString();const VV='/web/videos/';const vids=[{id:now+200+s,title:'沉浸式发动机积碳清洗解压必看',content:'#发动机清洗 #积碳 #解压',video_url:VV+'04_dent_repair.mp4',likes:6534+s*200,liked:false,playing:false,author:{username:'汽修小陈'},created_at:h(0.1)},{id:now+201+s,title:'全自动产线焊接机器人：工业之美',content:'#工业机器人 #焊装 #自动化',video_url:VV+'05_paint_touchup.mp4',likes:4567+s*100,liked:false,playing:false,author:{username:'智造前线'},created_at:h(0.2)},{id:now+202+s,title:'3分钟看完一台车从钣金到喷漆全过程',content:'#汽车制造 #涂装 #钣金喷漆',video_url:VV+'06_welding_qa.mp4',likes:12345+s*300,liked:false,playing:false,author:{username:'汽车工厂日记'},created_at:h(0.3)}];this.videoPosts=[...this.videoPosts,...vids]},async createPost(){this.creating=true;try{const form=new FormData();form.append('title',this.newPost.title);form.append('content',this.newPost.content);form.append('author_id','1');if(this.mediaFile){form.append(this.createType==='image'?'image_file':'video_file',this.mediaFile)}const{data}=await axios.post('/api/community/post',form);const newP={...data,liked:false,author:{username:'我'},image_url:this.mediaPreview||('https://picsum.photos/seed/user'+Date.now()+'/400/500')};this.posts.unshift(newP);if(newP.video_url)this.videoPosts.unshift({...newP,playing:false});this.showCreate=false;this.newPost={title:'',content:''};this.mediaFile=null;this.mediaPreview=null}catch(e){alert('发布失败: '+(e.response?.data?.detail||e.message))}finally{this.creating=false}},likePost(post){post.liked=!post.liked;post.likes=(post.likes||0)+(post.liked?1:-1)},openPost(post){this.selectedPost=post},onMediaSelect(e){const file=e.target.files[0];if(!file)return;this.mediaFile=file;const reader=new FileReader();reader.onload=ev=>{this.mediaPreview=ev.target.result};reader.readAsDataURL(file)},clearMedia(){this.mediaFile=null;this.mediaPreview=null;if(this.$refs.mediaInput)this.$refs.mediaInput.value=''},setVideoRef(el,idx){if(el)this.videoRefs[idx]=el},onVideoLoaded(idx){if(idx===0){const v=this.videoRefs[0];if(v){v.play().catch(()=>{});this.videoPosts[0].playing=true}}},togglePlay(idx){const video=this.videoRefs[idx];if(!video)return;if(video.paused){video.play().catch(()=>{});this.videoPosts[idx].playing=true}else{video.pause();this.videoPosts[idx].playing=false}},onVideoScroll(){const container=this.$refs.videoFeed;if(!container)return;const idx=Math.round(container.scrollTop/container.clientHeight);if(idx!==this.currentVideoIdx){const oldVid=this.videoRefs[this.currentVideoIdx];if(oldVid){oldVid.pause();this.videoPosts[this.currentVideoIdx].playing=false}this.currentVideoIdx=idx;const newVid=this.videoRefs[idx];if(newVid){newVid.play().catch(()=>{});this.videoPosts[idx].playing=true}}},formatTime(t){if(!t)return'';const d=new Date(t);return d.toLocaleDateString('zh-CN',{month:'short',day:'numeric'})}},watch:{tab(val){if(val==='video'){this.$nextTick(()=>{if(this.videoPosts.length>0&&this.videoRefs[0]){this.videoRefs[0].play().catch(()=>{});this.videoPosts[0].playing=true}})}}},mounted(){}}
