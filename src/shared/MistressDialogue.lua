-- Dialogue of the first mistress (Regular Dad) at her table. Structure only comes from the md: «В диалоге у стола можно
-- узнать местоположение отца, кто дома, сравнить входы и получить список необходимых действий», and the mistress reports
-- the recommended run N and strength M with the consequences of falling short.
-- PROVISIONAL TEXT: the md says "ветки реплик, последствия выбора ... ещё не утверждены" and asks whether answers change the
-- plan or reward (open question 10), so no choice changes anything except accepting the plan. Replace the wording freely.
-- Placeholders {N} and {M} are filled on the server from the player's HeistTarget values.
local nodes = {
	start = {
		text = "Значит, ты за моим Regular Dad. Садись. Что хочешь знать?",
		choices = {
			{ text = "Где он сейчас?", next = "where" },
			{ text = "Кто сейчас дома?", next = "who" },
			{ text = "Как попасть внутрь?", next = "entrances" },
			{ text = "Что мне нужно сделать?", next = "tasks" },
			{ text = "Насчёт бега и силы?", next = "stats" },
			{ text = "Я пойду.", next = "bye" },
		},
	},
	where = {
		text = "Он наверху, в комнате отдыха, с кружкой у столика у окна. К нему можно со стороны холла и с балкона.",
		choices = { { text = "Понятно. Другой вопрос.", next = "start" } },
	},
	who = {
		text = "Жена ходит кухня — столовая — гостиная и обратно, с паузами. Сын бродит между комнатой, холлом, лестницей и гостиной.",
		choices = { { text = "Понятно. Другой вопрос.", next = "start" } },
	},
	entrances = {
		text = "Два пути. А: найди запасной ключ в сарае на участке и зайди через постирочную. Б: возьми у мастера приставную лестницу и поставь её под балконом. Хватит одного, можно оба.",
		choices = { { text = "Понятно. Другой вопрос.", next = "start" } },
	},
	tasks = {
		text = "Возьми мешок в хозяйственном магазине. Потом подготовь хотя бы один путь внутрь. Всё запишется в твой блокнот. Берёшься?",
		choices = {
			{ text = "Берусь.", next = "accepted", effect = "AcceptPlan" },
			{ text = "Ещё подумаю.", next = "start" },
		},
	},
	stats = {
		text = "Бег советую от {N}: меньше — семье проще тебя догнать. Силу от {M}: меньше — мешок понесёшь очень медленно. Это совет, не запрет: на хитрости и укрытиях тоже можно выехать.",
		choices = { { text = "Понятно. Другой вопрос.", next = "start" } },
	},
	accepted = {
		text = "Тогда за дело. Блокнот у тебя на [N]. Когда отец будет в мешке и хвоста за тобой не будет — заходи.",
		choices = { { text = "Хорошо.", next = "bye" } },
	},
	bye = { text = "Удачи.", choices = {}, ends = true },
}

return { Start = "start", Nodes = nodes }
