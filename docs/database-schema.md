# Схема базы данных

В PostgreSQL хранятся пользователи, лекции, конспекты и тесты.
Файлы и картинки лежат в MinIO, сессии и очередь задач в Redis.
Там же 30 минут хранятся хеши одноразовых ссылок восстановления пароля.

На диаграмме показаны все поля и связи. PK означает первичный ключ,
FK означает ссылку на другую таблицу, UK означает уникальное значение.

```mermaid
erDiagram
    users ||--o{ materials : uploads
    materials |o--o{ materials : copied_from
    quizzes |o--o{ materials : included_in_package
    users ||--o{ notes : owns
    users ||--o{ material_images : owns
    users ||--o{ quizzes : owns
    materials ||--o| notes : has
    materials ||--o{ material_images : contains
    materials ||--o{ quizzes : has
    quizzes ||--o{ questions : contains
    questions ||--o{ answers : contains
    users ||--o{ quiz_attempts : completes
    materials ||--o{ quiz_attempts : has
    quizzes |o--o{ quiz_attempts : records

    quiz_attempts {
        uuid id PK "UUID попытки"
        uuid user_id FK "Пользователь"
        uuid material_id FK "Материал; допускает NULL"
        uuid quiz_id FK "Исходный тест; допускает NULL"
        boolean is_public_attempt "Попытка публичного теста"
        uuid run_id UK "Тренировка; допускает NULL"
        integer duration_ms "Время прохождения; допускает NULL"
        float8 score "Доля правильных ответов от 0 до 1"
        integer total "Количество вопросов"
        integer correct "Количество правильных ответов"
        jsonb quiz_snapshot "Копия вопросов и вариантов"
        jsonb answers "Выбранные варианты"
        jsonb results "Правильность и объяснения"
        timestamptz created_at "Дата прохождения"
    }
    users {
        uuid id PK "UUID пользователя"
        varchar first_name "Имя"
        varchar last_name "Фамилия"
        varchar email UK "Уникальный email"
        varchar hashed_password "Хеш пароля"
        boolean is_active "Активен ли аккаунт"
        timestamptz created_at "Дата создания"
        timestamptz updated_at "Дата обновления"
    }
    materials {
        uuid id PK "UUID материала"
        uuid user_id FK "Владелец: users.id"
        varchar original_filename "Название файла"
        boolean is_favorite "Добавлен в избранное"
        boolean is_public "Материал опубликован целиком"
        varchar public_title "Название в сообществе; допускает NULL"
        timestamptz published_at "Дата публикации; допускает NULL"
        uuid published_quiz_id FK "Тест в пакете; допускает NULL"
        uuid source_material_id FK "Источник копии; допускает NULL"
        varchar source_author "Автор источника; допускает NULL"
        timestamptz deleted_at "Дата удаления из библиотеки; допускает NULL"
        varchar s3_key "Ключ объекта в MinIO"
        varchar content_type "MIME-тип файла"
        integer size_bytes "Размер в байтах"
        materialstatus status "uploaded / processing / done / failed"
        timestamptz created_at "Дата создания"
        timestamptz updated_at "Дата обновления"
    }
    notes {
        uuid id PK "UUID конспекта"
        uuid material_id FK,UK "Материал: materials.id"
        uuid user_id FK "Владелец: users.id"
        text content "Содержимое конспекта"
        varchar llm_model "Модель генерации"
        integer generation_time_ms "Длительность в миллисекундах"
        float8 validation_score "Допускает NULL"
        timestamptz created_at "Дата создания"
        timestamptz updated_at "Дата обновления"
    }
    material_images {
        uuid id PK "UUID изображения"
        uuid material_id FK "Материал: materials.id"
        uuid user_id FK "Владелец: users.id"
        integer order "Номер внутри материала"
        varchar s3_key "Ключ изображения в MinIO"
        varchar mime_type "MIME-тип изображения"
        timestamptz created_at "Дата создания"
        timestamptz updated_at "Дата обновления"
    }
    quizzes {
        uuid id PK "UUID теста"
        uuid material_id FK "Материал: materials.id"
        uuid user_id FK "Владелец: users.id"
        boolean is_public "Опубликован ли тест"
        varchar public_title "Название в сообществе; допускает NULL"
        timestamptz published_at "Дата публикации; допускает NULL"
        quizstatus status "processing / done / failed"
        timestamptz created_at "Дата создания"
        timestamptz updated_at "Дата обновления"
    }
    questions {
        uuid id PK "UUID вопроса"
        uuid quiz_id FK "Тест: quizzes.id"
        text text "Текст вопроса"
        questiontype question_type "single / multiple"
        integer order "Порядок в тесте"
    }
    answers {
        uuid id PK "UUID варианта ответа"
        uuid question_id FK "Вопрос: questions.id"
        text text "Текст варианта"
        boolean is_correct "Правильный ли вариант"
        text explanation "Объяснение; допускает NULL"
    }
```

## Как это устроено

- `users`: аккаунты пользователей.
- `materials`: загруженные лекции. В таблице хранится информация о файле и его ключ в MinIO.
- `notes`: конспект лекции. У одной лекции может быть только один конспект.
- `material_images`: картинки из лекции. Номер картинки уникален внутри лекции.
- `quizzes`: тесты по лекции. У одной лекции может быть несколько тестов.
- `questions`: вопросы теста. Тип `single` означает один правильный ответ, `multiple` означает несколько.
- `answers`: варианты ответов, отметка правильности и объяснение.
- `quiz_attempts`: завершённые попытки с датой, оценкой, вопросами и выбранными ответами.

## Что важно знать

NULL допускается в `validation_score`, `explanation`, `materials.deleted_at`,
`quizzes.public_title`, `quizzes.published_at`, `quiz_attempts.quiz_id`,
`quiz_attempts.material_id`, `quiz_attempts.run_id` и `quiz_attempts.duration_ms`.
У `materials` также допускают NULL поля `public_title`, `published_at`,
`published_quiz_id`, `source_material_id` и `source_author`.
UUID создаёт приложение. Поля `created_at` и `updated_at` хранят время создания и обновления.
У вопросов и вариантов ответов этих дат нет.

При удалении пользователя удаляются связанные записи в БД.
При удалении лекции удаляются её конспект, картинки и тесты.
Файлы в MinIO нужно удалять отдельно.

Количество вопросов и правильных ответов проверяет приложение.
История сохраняется в `quiz_attempts`. В ней есть копия теста, выбранные варианты
и объяснения ошибок. Поэтому старую попытку можно открыть даже после изменения
или удаления исходного теста. При удалении теста `quiz_id` становится NULL.
При удалении участника удаляются его попытки. Удаление автора или лекции
не удаляет сохранённые публичные попытки других участников.
Для списка попыток есть индекс по пользователю, материалу и дате.
У попытки есть `created_at`, но нет `updated_at`.

Избранное хранится в `materials.is_favorite`. Удаление из библиотеки устанавливает
`deleted_at`: материал и связанные данные больше не выдаются через API.
Строки и файлы при этом остаются в хранилище.

Схема соответствует миграции `b6e1f4a8c015`.
Исходники: [модели](../app/models/) и [миграции](../alembic/versions/).


Публичность задаётся у конкретного теста полем `quizzes.is_public`.
Лекция и конспект от этого публичными не становятся.
У публичной попытки `user_id` указывает на участника, а не на автора теста.
При физическом удалении материала ссылка `quiz_attempts.material_id` становится NULL.
Сохранённые копии публичных попыток остаются у участников.


В сообществе публикуется весь материал: исходный файл, конспект, картинки
и готовый тест, если он есть. Публикация требует отдельного подтверждения владельца.
`materials.published_quiz_id` указывает на тест, включённый в пакет.
Кнопка «Обновить пакет» выбирает последний готовый тест.

При импорте создаются новые записи и отдельные объекты в MinIO.
Копия остаётся закрытой, результаты прохождений в неё не переносятся.
`source_material_id` и `source_author` сохраняют происхождение материала.
Частичный уникальный индекс `(user_id, source_material_id)` запрещает повторный
импорт активной копии. После удаления копии её можно импортировать снова.


Для тренировки на время сервер хранит в Redis начало и `run_id`.
Страница подтверждает активность каждые 30 секунд; без подтверждения попытка
истекает через 2 минуты. Закрытие страницы отправляет отмену, новый старт
заменяет незавершённую попытку. Прерванные попытки не попадают в рейтинг.
При завершении сохраняется `duration_ms`, уникальный `run_id` защищает
от повторного сохранения. Старые результаты без времени не раскрываются.
