# Лабораторная работа № 1 — FSM и Behavior Tree

Проект для дисциплины «Игровой искусственный интеллект» на основе [шаблона преподавателя](https://github.com/kolesnikov-vstu-gameai/lab01-fsm-bt).

**Студент:** [ФИО, группа] · **Стек:** Unity 6 (6000.3.9f1), C#, NavMesh · **Видео:** [добавить ссылку] · **Отчёт:** [docs/report.md](docs/report.md)

## Запуск

1. Откройте `unity/UnityProject` в Unity 6000.3.9f1.
2. Если сцены ещё нет, выберите **Lab 01 → Create demonstration scene**. Команда создаст комнату, четыре препятствия, четыре точки патруля, игрока, стражника и NavMesh.
3. Откройте `Assets/_Project/Scenes/Lab01.unity` и нажмите Play.
4. Управляйте игроком клавишами WASD. На объекте стражника в компоненте `GuardMode` выберите `FSM` или `BehaviorTree`.
5. Переходы выводятся в Console. Для обоих режимов проверьте Patrol → Alert → Chase → Attack и Chase → Search → Patrol.

## Что реализовано

- Видимость по дальности, углу обзора и raycast с учётом препятствий.
- Тревога 1 с до преследования, атака в пределах 1,5 м, потеря цели через 2 с и поиск 10 с.
- Поиск у последней известной позиции и обход четырёх соседних точек.
- Две отдельные реализации принятия решений на одной сцене.
- EditMode-тесты базовых узлов дерева поведения в `Assets/_Project/Tests/EditMode`.

## Структура

- `unity/UnityProject/Assets/_Project/Scripts/AI` — сенсор, движение и FSM.
- `unity/UnityProject/Assets/_Project/Scripts/BT` — узлы дерева и BT стражника.
- `unity/UnityProject/Assets/_Project/Editor/CreateLabScene.cs` — генератор сцены.
- `docs/report.md` и `docs/diagrams.md` — черновик отчёта и диаграммы.

## Сдача

Перед сдачей заполните личные данные, проведите проверку в Unity, добавьте скриншоты и ссылку на видео в README и отчёт. Перенесите отчёт в официальный шаблон кафедры, экспортируйте `docs/report.pdf`, создайте тег `v1.0` и GitHub Release в своём репозитории. Для GitHub Actions нужен секрет `UNITY_LICENSE`.
