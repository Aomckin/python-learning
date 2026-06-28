def get_energy(player):
    return player.energy


def get_max_energy(player):
    return player.max_energy


def get_exp(player):
    return getattr(player, "exp", 0)


def get_coin(player):
    return getattr(player, "coin", 0)


def get_action_counts(player):
    return getattr(player, "action_counts", {})


def get_done_task_count(player):
    return getattr(player, "done_task_count", 0)


def get_done_special_task_count(player):
    return getattr(player, "done_special_task_count", 0)


def get_unlocked_achievement_ids(player):
    return set(getattr(player, "unlocked_achievements", []))


def get_unlocked_title_ids(player):
    return set(getattr(player, "unlocked_titles", []))


def get_equipped_title_id(player):
    return getattr(player, "equipped_title", "")


def get_special_task_slots(player):
    return getattr(player, "special_task_slots", 1)


def has_daily_double_exp(player, today):
    return getattr(player, "daily_double_exp_date", "") == today


def clamp_energy(player):
    max_energy = getattr(player, "max_energy", None)
    if max_energy is None and hasattr(player, "config"):
        max_energy = player.config["max_energy"]

    player.energy = max(0, min(max_energy, player.energy))


def add_energy(player, value):
    player.energy += value
    clamp_energy(player)


def add_exp(player, value):
    player.exp += value


def add_coin(player, value):
    player.coin += value


def spend_coin(player, value):
    if player.coin < value:
        return False

    player.coin -= value
    return True


def unlock_achievement(player, achievement_id):
    if achievement_id not in player.unlocked_achievements:
        player.unlocked_achievements.append(achievement_id)


def unlock_title(player, title_id):
    if title_id not in player.unlocked_titles:
        player.unlocked_titles.append(title_id)


def equip_title(player, title_id):
    player.equipped_title = title_id


def increment_action(player, action_name):
    player.action_counts[action_name] = (
        player.action_counts.get(action_name, 0) + 1
    )


def increment_task_done(player):
    player.done_task_count += 1


def increment_special_task_done(player):
    player.done_special_task_count += 1


def increment_timed_action(player):
    player.completed_timed_actions += 1


def add_daily_task_reward(player, reward, exp):
    add_energy(player, reward)
    add_exp(player, exp)
    increment_task_done(player)


def add_special_task_reward(player, coin, exp):
    add_coin(player, coin)
    add_exp(player, exp)
    increment_special_task_done(player)


def add_action_result(player, action_name, energy_change, exp_reward=0):
    add_energy(player, energy_change)
    add_exp(player, exp_reward)
    increment_action(player, action_name)


def complete_action(player, action_name, energy_change, exp_reward=0):
    add_action_result(player, action_name, energy_change, exp_reward)


def complete_timed_action(
        player,
        action_name,
        duration_minutes,
        energy_change,
        exp_reward
):
    add_action_result(player, action_name, energy_change)
    add_exp(player, exp_reward)
    increment_timed_action(player)

    return {
        "action_name": action_name,
        "duration_minutes": duration_minutes,
        "energy_change": energy_change,
        "exp_change": exp_reward,
        "current_energy": player.energy,
    }


def grant_daily_task_reward(player, reward, exp, task_name):
    add_daily_task_reward(player, reward, exp)


def grant_special_task_reward(player, coin, exp, task_name):
    add_special_task_reward(player, coin, exp)


def record_shop_purchase(player, item, today):
    item_id = item.get("id")
    stock_type = item.get("stock_type", "infinite")

    if stock_type == "daily":
        player.shop_daily_purchases.setdefault(today, {})
        player.shop_daily_purchases[today][item_id] = (
            player.shop_daily_purchases[today].get(item_id, 0) + 1
        )

    if stock_type == "permanent":
        player.shop_total_purchases[item_id] = (
            player.shop_total_purchases.get(item_id, 0) + 1
        )


def record_purchase(player, item, today):
    record_shop_purchase(player, item, today)


def apply_shop_effect(player, item, today):
    effect_type = item.get("effect_type")
    effect_value = item.get("effect_value", 0)

    if effect_type == "daily_double_exp":
        player.daily_double_exp_date = today

    if effect_type == "special_task_slot":
        player.special_task_slots += effect_value

    if effect_type == "unlock_title":
        unlock_title(player, effect_value)
