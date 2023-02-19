# TLab 2023. NLP - Тестовое задание

Репозиторий содержит результаты использования промптов Chain-of-Thoughts с использованием greedy decoding и self-consistency методов на модели BLOOM-176B.

## Оглавление:
1. Параметры генерации.
2. Результаты.
3. Обсуждение.
4. Выводы.
5. Ссылки.
6. Как запустить код.
## Параметры генерации
Параметры генерации для self-consistency: 
1. `max_new_tokens=128` - такое значение было выбрано, потому что по нескольким опытам при меньшем значении ответ не до конца генерировался. Соответственно, часть ответов могла потеряться. Значение больше не было взято по причине долгой генерации и при большом количестве токенов модель начинает сама придумывать вопросы.
2. `temperature=0.9` - такое значение температуры из-за того, чтобы генерировать разнообразные ответы. На самом деле я не увидел особых отличий при изменении значения с 0.7 до 0.9. Вполне возможно, что результаты могут измениться при более низких значениях, но тогда ответы модели будут повторяться. Повторы чреваты тем, что правильные ответы могут быть не даны вовсе.
3. `top_k=32` - на самом деле этот параметр я особо не подбирал. Я смотрел на это значение и значение выше, и мне показалось, что при указанном параметре ответы реже уходят в неправильные рассуждения.

Для greedy метода я оставил `max_new_tokens=128`.

Промпты были такими же, какие они были в [1]. Я решил оставить их по той причине, чтобы воспроизвести результаты точь-в-точь за исключением параметров генерации. 

## Результаты
Всего я генерировал 5 ответов, т.к. при большем количестве модель бы работала намного дольше. Из всего тестового набора мне удалось провести эксперименты только на 25 примерах. Так получилось из-за того что для модели не хватало серверов для выполнения инференса. В ответах на вопрос с помощью алгоритма, который представлен в [2], в качестве правильного ответа я выбирал наиболее частый ответ. Результаты получились такими:
| model                  | method           | correct | total | accuracy |
|------------------------|------------------|---------|-------|----------|
| BLOOM-176B             | CoT-prompting    | 3       | 25    | 0.12     |
|                        | self-consistency | 4       | 25    | 0.16     |
| LaMDA-137B             | CoT-prompting    | -       | -     | 0.17     |
|                        | self-consistency | -       | -     | 0.28     |
| GPT-3 Code-davinci-001 | CoT-prompting    | -       | -     | 0.15     |
|                        | self-consistency | -       | -     | 0.23     |
| GPT-3 Code-davinci-002 | CoT-prompting    | -       | -     | 0.60     |
|                        | self-consistency | -       | -     | 0.78     |

Как видно по таблице, BLOOM-176B уступает другим моделям, которые имеют примерно одинаковое количество параметров. Тем не менее проведено довольно мало экспериментов, чтобы делать какие-то выводы относительно качества модели.

## Обсуждение
Довольно тяжело говорить про качество модели в целом, но у меня есть ощущение, что self-consistency работает всё-таки лучше. Потому что у некоторых вопросов были такие ситуации, когда были ответы с правильным рассуждением, но из-за какой-то ошибки получался неправильный результат. Как правило, ошибки были трёх типов:
1. Ошибка в вычислении
2. Ошибка в рассуждении
3. Несоответствие ответа шаблону

### Ошибка в вычислении
Мне попадались случаи, когда модель рассуждала верно, но итоговый ответ она посчитала неправильно. Скорее всего такая ситуация связана с тем, что модель не умеет считать некоторые примеры, потому что в других ситуациях ответы подсчитывались верно. Поскольку в модели не заложен математический аппарат, то решить эту проблему можно тем, чтобы дать ей калькулятор эксплицитно. Т.е. можно попробовать парсить результирующее математическое выражение и либо передавать его какому-нибудь онлайн-калькулятору, либо написать собственный калькулятор. Идея такого подхода описана в . Пример неправильного вычисления:
```
Вопрос:
Eliza's rate per hour for the first 40 hours she works each week is $10. She also receives an overtime pay of 1.2 times her regular hourly rate. If Eliza worked for 45 hours this week, how much are her earnings for this week?
Ответ:
The regular hourly rate for the first 40 hours she works each week is $10, and for the next 5 hours it is 1.2 times $10, which is $12. This means she gets $12 per hour for the final 5 hours she works. So, in total we have $10 * 40 + $12 * 5 = $440 for her earnings for this week. The answer is $440.
```

### Ошибка в рассуждении
Есть случаи, когда модель не совсем понимала условие задачи из-за чего в рассуждении оказывались ошибки. Эти ошибки в итоге приводили к неправильным ответам. Пример такого рассуждения:
```
Вопрос:
Toulouse has twice as many sheep as Charleston. Charleston has 4 times as many sheep as Seattle. How many sheep do Toulouse, Charleston, and Seattle have together if Seattle has 20 sheep?
Ответ:
We want to know how many sheep they all have together. We already know that Toulouse has twice as many as Charleston and Charleston has 4 times as many as Seattle, so the following can be used to figure that out:
  Toulouse:             2 * 4 =    8
  Charleston:            4 * 20 =  80
  Seattle:                20
  Total:                 8 + 80 + 20 = 108
```

### Несоответствие ответа шаблону
Часть ответов не соответствовала шаблону из-за чего ответ мог не распознаться. По этой причине правильный ответ может проигнорироваться. Не всегда можно предугадать ответ модели, поэтому какой-то общий шаблон придумать проблематично. Возможно имеет смысл дать больше примеров или в промпте прямо сказать, что ответ должен быть в конкретном виде. Тем не менееможно ещё посмотреть примеры с нешаблонными ответами и постараться выделить какой-то более общий паттерн и написать регулярное выражение. Пример такого ответа:
```
We start off with the total number of pastries. 3 dozen donuts, 2 dozen mini cupcakes and 6 dozen mini cheesecakes. So we have 3 + 2 + 6 = 11 dozen. We divide it by the number of different types of pastries. 3 + 2 + 6 = 11 so we have 11 / 3 = 3.33 times. So 3.33 times $68 + 3.33 times $80 + 3.33 times $55 = $245.33
The total cost was $245.33.
```

### Проблема генерации
Я предполагаю, что такое плохое качество ответов получилось из-за того, что количество сгенерированных ответов было сильно ограниченным. В [2] авторы использовали 40 ответов, тогда как в моих экспериментов было только 5. Соответственно, при таком количестве страдает степень уверенности выбора ответа. Также из-за ограниченности ресурсов и времени не был проведён эксперимент с использованием весов для каждого ответа. Тем не менее, судя по статье, веса ответов для математических задач не играют важной роли.

## Выводы
На выборке из одинаковых 25 примеров Chain-of-Thoughts с использованием метода self-consistency показывает результаты лучше, чем использование greedy decoding. При этом оба метода уступают в качестве моделям, приведённых в [2]. Тем не менее делать какие-то определённые выводы трудно, поскольку размер выборки довольно мал. В ходе анализа ответов модели были обнаружены самые частые ошибки, связынные с вычислениями, рассуждением и несоответствием шаблону. Дальнейшие исследования могут быть направлены на то, чтобы научить модель правильно производить вычисления и более точно выделять ответ.

## Ссылки
1. Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou. Chain of thought prompting elicits reasoning in large language models. Conference on Neural Information Processing Systems (NeurIPS), 2022. URL: https://arxiv.org/pdf/2201.11903.
2. Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed H. Chi, Sharan Narang, Aakanksha Chowdhery, Denny Zhou. Self-Consistency Improves Chain of Thought Reasoning in Language Models. URL: https://arxiv.org/pdf/2203.11171.pdf.
3. Timo Schick, Jane Dwivedi-Yu, Roberto Dessì, Roberta Raileanu, Maria Lomeli, Luke Zettlemoyer, Nicola Cancedda, Thomas Scialom. Toolformer: Language Models Can Teach Themselves to Use Tools. URL: https://arxiv.org/pdf/2302.04761.pdf.

## Как запустить код
1. Ресурсы компьютеры должны соответствовать требованию проекта https://github.com/bigscience-workshop/petals.
2. Выполнить `sh init.sh`.
3. Запускать проект с помощью команды python `run.py -t <название задачи> -m <название метода>`.
   1. Допустимые задачи:
      1. experiment - запускает эксперимент.
      2. evaluation - запускает оценку результатов. Можно давать в -m несколько методов через пробел.
      3. answers - показывает ответы.
   2. Допустимые названия методов:
      1. self_consistency - использование метода self-consistency.
      2. greedy - использование метода greedy decoding.

Например, команда `python run.py -m greedy self_consistency -t evaluation` запустит оценку результатов для greedy decoding и self-consistency методов и выведет таблицу.

Команда `python run.py -m self_consistency -t experiment` запустит выполнение экспериментов для self-consistency метода и каждую генерацию ответов для вопроса сохранит в файл.