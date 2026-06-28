const TIMER_SECOND_SCALE = 1;

const stateEls = {
    energy: document.getElementById("energy"),
    exp: document.getElementById("exp"),
    level: document.getElementById("level"),
    coin: document.getElementById("coin"),
    title: document.getElementById("title"),
};

const actionsEl = document.getElementById("actions");
const dailyTasksEl = document.getElementById("dailyTasks");
const specialTasksEl = document.getElementById("specialTasks");
const shopEl = document.getElementById("shop");
const achievementsEl = document.getElementById("achievements");
const titlesEl = document.getElementById("titles");
const logsEl = document.getElementById("logs");
const resultEl = document.getElementById("result");
const refreshButton = document.getElementById("refreshButton");
const refreshTasksButton = document.getElementById("refreshTasksButton");
const openShopButton = document.getElementById("openShopButton");
const openAchievementsButton = document.getElementById("openAchievementsButton");
const openTitlesButton = document.getElementById("openTitlesButton");
const shopDialog = document.getElementById("shopDialog");
const achievementsDialog = document.getElementById("achievementsDialog");
const titlesDialog = document.getElementById("titlesDialog");
const durationPanel = document.getElementById("durationPanel");
const durationActionName = document.getElementById("durationActionName");
const durationOptions = document.getElementById("durationOptions");
const durationCancelButton = document.getElementById("durationCancelButton");
const timerPanel = document.getElementById("timerPanel");
const timerActionName = document.getElementById("timerActionName");
const timerTotal = document.getElementById("timerTotal");
const timerRemaining = document.getElementById("timerRemaining");
const timerStatus = document.getElementById("timerStatus");
const pauseTimerButton = document.getElementById("pauseTimerButton");
const resumeTimerButton = document.getElementById("resumeTimerButton");
const abandonTimerButton = document.getElementById("abandonTimerButton");

let actionButtons = [];
let choosingActionName = null;
let currentTimer = null;

// 最小版限制：页面刷新后不恢复旧计时器，也不会自动结算未完成行动。
function setResult(message, kind) {
    resultEl.textContent = message;
    resultEl.className = `result ${kind || ""}`.trim();
}

async function requestJson(url, options) {
    let response;
    try {
        response = await fetch(url, options);
    } catch (error) {
        throw new Error(`请求失败：${error.message}`);
    }

    const text = await response.text();
    let data = {};
    try {
        data = text ? JSON.parse(text) : {};
    } catch (error) {
        throw new Error(`响应不是 JSON：${text.slice(0, 200)}`);
    }

    if (!response.ok) {
        throw new Error(data.message || data.detail || `HTTP ${response.status}`);
    }

    return data;
}

async function executeCommand(type, payload = {}, button = null) {
    const oldText = button ? button.textContent : "";
    try {
        if (button) {
            button.disabled = true;
            button.textContent = "请求处理中...";
        }
        setResult("请求处理中...", "");
        const result = await requestJson("/command", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({type, payload}),
        });
        await applyCommandResult(result);
        return result;
    } catch (error) {
        setResult(error.message, "error");
        return null;
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = oldText;
        }
    }
}

function renderState(state) {
    stateEls.energy.textContent = state.energy_text || `${state.energy_value ?? "-"} / ${state.energy_max ?? "-"}`;
    stateEls.exp.textContent = state.exp_text || "-";
    stateEls.level.textContent = state.level_text || "-";
    stateEls.coin.textContent = state.coin_text || "-";
    stateEls.title.textContent = state.title_text || "-";
    renderActions(state.action_views);
    renderDailyTasks(state.active_task_views);
    renderSpecialTasks(state.active_special_task_views);
    renderShop(state.shop_category_views);
    renderAchievements(state.achievement_sections);
    renderTitles(state.title_views);
    renderLogs(state.logs);
}

function renderActions(actions) {
    actionsEl.innerHTML = "";
    actionButtons = [];

    if (!Array.isArray(actions) || actions.length === 0) {
        renderEmpty(actionsEl, "暂无行动");
        return;
    }

    actions.forEach((action) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = action.button_text || action.name || "未知行动";
        button.title = buildActionTitle(action);
        button.disabled = !action.name || isActionBusy();
        button.addEventListener("click", () => loadDurationOptions(action));
        actionsEl.appendChild(button);
        actionButtons.push(button);
    });
}

function renderDailyTasks(taskViews) {
    renderTaskCards(dailyTasksEl, taskViews, "暂无每日任务", "COMPLETE_DAILY_TASK");
}

function renderSpecialTasks(taskViews) {
    renderTaskCards(specialTasksEl, taskViews, "暂无特殊任务", "COMPLETE_SPECIAL_TASK");
}

function renderTaskCards(container, taskViews, emptyText, commandType) {
    container.innerHTML = "";
    if (!Array.isArray(taskViews) || taskViews.length === 0) {
        renderEmpty(container, emptyText);
        return;
    }

    taskViews.forEach((task) => {
        const card = document.createElement("article");
        card.className = `task-card ${task.button_state === "normal" ? "" : "locked"}`.trim();
        appendText(card, "h3", task.name || task.id || "未知任务");
        appendText(card, "p", task.detail_text || task.reward_text || "暂无详情");
        const button = makeCommandButton(task.button_text || "完成", task.button_state, commandType, task.command_payload || {});
        card.appendChild(button);
        container.appendChild(card);
    });
}

function renderShop(shopCategoryViews) {
    shopEl.innerHTML = "";
    if (!Array.isArray(shopCategoryViews) || shopCategoryViews.length === 0) {
        renderEmpty(shopEl, "暂无商品");
        return;
    }

    shopCategoryViews.forEach((categoryView) => {
        const section = document.createElement("section");
        section.className = "shop-category";
        appendText(section, "h3", categoryView.category || "未分类");

        const items = Array.isArray(categoryView.items) ? categoryView.items : [];
        if (items.length === 0) {
            renderEmpty(section, "敬请期待");
        } else {
            items.forEach((item) => {
                const card = document.createElement("article");
                card.className = `shop-item ${item.button_state === "normal" ? "" : "locked"}`.trim();
                appendText(card, "h4", item.name || item.id || "未知商品");
                appendText(card, "p", item.desc || "暂无描述");
                appendText(card, "p", `价格：${item.price ?? 0} 金币 / ${item.stock_text || "库存未知"}`);
                card.appendChild(makeCommandButton(item.button_text || "购买", item.button_state, "BUY_SHOP_ITEM", item.command_payload || {}));
                section.appendChild(card);
            });
        }
        shopEl.appendChild(section);
    });
}

function renderAchievements(achievementSections) {
    achievementsEl.innerHTML = "";
    if (!Array.isArray(achievementSections) || achievementSections.length === 0) {
        renderEmpty(achievementsEl, "暂无成就数据");
        return;
    }

    achievementSections.forEach((section) => {
        const group = document.createElement("section");
        group.className = "achievement-section";
        appendText(group, "h3", section.title || section.id || "成就");
        const items = Array.isArray(section.items) ? section.items : [];
        if (items.length === 0) {
            renderEmpty(group, section.empty_text || "暂无数据");
        } else {
            items.forEach((achievement) => {
                const card = document.createElement("article");
                card.className = `achievement-card ${section.id === "locked" ? "locked" : ""}`.trim();
                appendText(card, "h4", achievement.name || achievement.id || "未知成就");
                appendText(card, "p", achievement.desc || achievement.condition_text || "");
                appendText(card, "p", achievement.reward_text || "无奖励");
                group.appendChild(card);
            });
        }
        achievementsEl.appendChild(group);
    });
}

function renderTitles(titleViews) {
    titlesEl.innerHTML = "";
    if (!Array.isArray(titleViews) || titleViews.length === 0) {
        renderEmpty(titlesEl, "暂无称号数据");
        return;
    }

    titleViews.forEach((title) => {
        const card = document.createElement("article");
        const equipped = title.button_text === "已佩戴" || title.status_text === "已佩戴";
        card.className = `title-card ${title.section === "locked" ? "locked" : ""} ${equipped ? "equipped" : ""}`.trim();
        appendText(card, "h3", title.name || title.id || "未知称号");
        appendText(card, "p", title.display_text || title.desc || title.condition_text || "暂无详情");
        appendText(card, "p", title.bonus_text || "");
        card.appendChild(makeCommandButton(title.button_text || "佩戴", title.button_state, "EQUIP_TITLE", title.command_payload || {}));
        titlesEl.appendChild(card);
    });
}

function renderLogs(logs) {
    if (!Array.isArray(logs) || logs.length === 0) {
        logsEl.textContent = "暂无日志";
        return;
    }

    logsEl.innerHTML = "";
    logs.slice(-50).forEach((log) => {
        const item = document.createElement("div");
        item.textContent = String(log);
        logsEl.appendChild(item);
    });
    logsEl.scrollTop = logsEl.scrollHeight;
}

function openDialog(dialog) {
    if (dialog && !dialog.open) {
        dialog.showModal();
    }
}

function makeCommandButton(text, buttonState, commandType, payload) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.disabled = buttonState !== "normal";
    button.addEventListener("click", () => executeCommand(commandType, payload, button));
    return button;
}

function appendText(parent, tagName, text) {
    if (text === undefined || text === null || text === "") {
        return null;
    }
    const element = document.createElement(tagName);
    element.textContent = String(text);
    parent.appendChild(element);
    return element;
}

function renderEmpty(container, message) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = message;
    container.appendChild(empty);
}

function buildActionTitle(action) {
    const parts = [];
    if (action.energy_change !== undefined) {
        parts.push(`能量变化：${action.energy_change}`);
    }
    if (action.exp_change !== undefined) {
        parts.push(`基础经验：${action.exp_change}`);
    }
    return parts.join(" / ");
}

function isActionBusy() {
    return Boolean(choosingActionName || currentTimer);
}

function setActionButtonsDisabled(disabled) {
    actionButtons.forEach((button) => {
        button.disabled = disabled;
    });
}

async function loadState(button) {
    const oldText = button ? button.textContent : "";
    try {
        if (button) {
            button.disabled = true;
            button.textContent = "请求处理中...";
        }
        setResult("请求处理中...", "");
        const state = await requestJson("/state");
        renderState(state);
        setResult("状态已刷新", "success");
    } catch (error) {
        setResult(error.message, "error");
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = oldText;
        }
        setActionButtonsDisabled(isActionBusy());
    }
}

async function loadDurationOptions(action) {
    if (!action.name || isActionBusy()) {
        return;
    }

    choosingActionName = action.name;
    setActionButtonsDisabled(true);
    hideDurationPanel();
    setResult("请求处理中...", "");

    try {
        const result = await requestJson(`/actions/${encodeURIComponent(action.name)}/duration-options`);
        const options = extractDurationOptions(result);
        if (options.length === 0) {
            throw new Error("后端未返回可选时长");
        }
        renderDurationOptions(action.name, options);
        setResult(result.message || "请选择行动时长", result.success === false ? "error" : "success");
    } catch (error) {
        choosingActionName = null;
        hideDurationPanel();
        setActionButtonsDisabled(false);
        setResult(error.message, "error");
    }
}

function extractDurationOptions(result) {
    const events = Array.isArray(result.events) ? result.events : [];
    const event = events.find((item) => item.type === "ACTION_DURATION_OPTIONS");
    const options = event && event.payload ? event.payload.options : result.options;
    return Array.isArray(options) ? options : [];
}

function renderDurationOptions(actionName, options) {
    durationActionName.textContent = actionName;
    durationOptions.innerHTML = "";

    options.forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = option.label || `${option.minutes} 分钟`;
        button.title = `倍率：${option.multiplier ?? 1}`;
        button.addEventListener("click", () => startTimer(actionName, option));
        durationOptions.appendChild(button);
    });

    durationPanel.classList.remove("hidden");
}

function hideDurationPanel() {
    durationPanel.classList.add("hidden");
    durationActionName.textContent = "-";
    durationOptions.innerHTML = "";
}

function cancelDurationSelection() {
    choosingActionName = null;
    hideDurationPanel();
    setActionButtonsDisabled(false);
    setResult("已取消选择时长", "");
}

function startTimer(actionName, option) {
    clearTimerState(false);
    choosingActionName = null;
    hideDurationPanel();

    const minutes = Number(option.minutes);
    const safeMinutes = Number.isFinite(minutes) && minutes > 0 ? minutes : 1;
    const totalSeconds = Math.max(1, Math.round(safeMinutes * 60 * TIMER_SECOND_SCALE));
    currentTimer = {
        actionName,
        option,
        totalSeconds,
        remainingSeconds: totalSeconds,
        status: "running",
        intervalId: null,
        completed: false,
    };

    setActionButtonsDisabled(true);
    renderTimer();
    startTimerInterval();
    setResult("番茄钟已开始", "success");
}

function startTimerInterval() {
    if (!currentTimer) {
        return;
    }
    stopTimerInterval();
    currentTimer.intervalId = window.setInterval(tickTimer, 1000);
}

function stopTimerInterval() {
    if (currentTimer && currentTimer.intervalId) {
        window.clearInterval(currentTimer.intervalId);
        currentTimer.intervalId = null;
    }
}

function tickTimer() {
    if (!currentTimer || currentTimer.status !== "running") {
        return;
    }

    currentTimer.remainingSeconds = Math.max(0, currentTimer.remainingSeconds - 1);
    renderTimer();

    if (currentTimer.remainingSeconds === 0) {
        completeTimedAction();
    }
}

function pauseTimer() {
    if (!currentTimer || currentTimer.status !== "running") {
        return;
    }
    currentTimer.status = "paused";
    stopTimerInterval();
    renderTimer();
}

function resumeTimer() {
    if (!currentTimer || currentTimer.status !== "paused") {
        return;
    }
    currentTimer.status = "running";
    startTimerInterval();
    renderTimer();
}

async function completeTimedAction() {
    if (!currentTimer || currentTimer.completed) {
        return;
    }

    currentTimer.completed = true;
    currentTimer.status = "settling";
    stopTimerInterval();
    renderTimer();
    setResult("请求处理中...", "");

    const timer = currentTimer;
    try {
        const result = await requestJson("/command", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                type: "COMPLETE_TIMED_ACTION",
                payload: {
                    action_name: timer.actionName,
                    option: timer.option,
                },
            }),
        });
        await applyCommandResult(result);
    } catch (error) {
        setResult(error.message, "error");
    } finally {
        clearTimerState(true);
    }
}

async function abandonTimer() {
    if (!currentTimer) {
        return;
    }

    const timer = currentTimer;
    const elapsedSeconds = timer.totalSeconds - timer.remainingSeconds;
    const elapsedMinutes = Math.floor(elapsedSeconds / 60);

    timer.status = "abandoning";
    stopTimerInterval();
    renderTimer();
    setResult("请求处理中...", "");

    try {
        const result = await requestJson("/command", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                type: "LOG_ABANDONED_ACTION",
                payload: {
                    action_name: timer.actionName,
                    elapsed_minutes: elapsedMinutes,
                },
            }),
        });
        await applyCommandResult(result);
    } catch (error) {
        setResult(error.message, "error");
    } finally {
        clearTimerState(true);
    }
}

async function applyCommandResult(result) {
    const lines = [
        result.success ? "成功" : "失败",
        result.message || "",
        ...formatEvents(result.events),
    ].filter(Boolean);
    setResult(lines.join("\n"), result.success ? "success" : "error");

    if (result.state) {
        renderState(result.state);
    } else {
        const state = await requestJson("/state");
        renderState(state);
    }
}

function formatEvents(events) {
    if (!Array.isArray(events)) {
        return [];
    }
    return events.map((event) => {
        const payload = event.payload || {};
        const text = payload.message || payload.name || payload.title || payload.id || "";
        const labels = {
            LEVEL_UP: "等级提升",
            ACHIEVEMENT_UNLOCK: "成就解锁",
            TITLE_UNLOCK: "称号解锁",
            TASK_COMPLETE: "任务完成",
            SHOP_PURCHASE: "购买成功",
            ERROR: "错误",
        };
        return `${labels[event.type] || event.type}${text ? `：${text}` : ""}`;
    });
}

function clearTimerState(restoreActions) {
    stopTimerInterval();
    currentTimer = null;
    timerPanel.classList.add("hidden");
    if (restoreActions) {
        setActionButtonsDisabled(false);
    }
}

function renderTimer() {
    if (!currentTimer) {
        timerPanel.classList.add("hidden");
        return;
    }

    timerPanel.classList.remove("hidden");
    timerActionName.textContent = currentTimer.actionName;
    timerTotal.textContent = `${Math.round(currentTimer.totalSeconds / TIMER_SECOND_SCALE / 60)} 分钟`;
    timerRemaining.textContent = formatSeconds(currentTimer.remainingSeconds);
    timerStatus.textContent = timerStatusText(currentTimer.status);

    pauseTimerButton.disabled = currentTimer.status !== "running";
    resumeTimerButton.disabled = currentTimer.status !== "paused";
    abandonTimerButton.disabled = ["settling", "abandoning"].includes(currentTimer.status);
}

function timerStatusText(status) {
    const labels = {
        running: "进行中",
        paused: "已暂停",
        settling: "结算中",
        abandoning: "放弃中",
    };
    return labels[status] || status;
}

function formatSeconds(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

durationCancelButton.addEventListener("click", cancelDurationSelection);
pauseTimerButton.addEventListener("click", pauseTimer);
resumeTimerButton.addEventListener("click", resumeTimer);
abandonTimerButton.addEventListener("click", abandonTimer);
refreshButton.addEventListener("click", () => loadState(refreshButton));
refreshTasksButton.addEventListener("click", () => executeCommand("REFRESH_DAILY_TASKS", {}, refreshTasksButton));
openShopButton.addEventListener("click", () => openDialog(shopDialog));
openAchievementsButton.addEventListener("click", () => openDialog(achievementsDialog));
openTitlesButton.addEventListener("click", () => openDialog(titlesDialog));
document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => {
        document.getElementById(button.dataset.closeDialog)?.close();
    });
});
loadState();
