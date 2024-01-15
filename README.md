Тестовое задание для соискателей на позицию Senior DE

1. Решение находится в папке /endpoint
Для развёртывания в Docker-контейнере нужно:

1.1. Отредактировать файл "compose.yaml", задав в переменных среды необходимые значения для подключения к СУБД:
	- DB_HOST 		- имя хоста
    - DB_PORT		- порт для подключения
    - DB_DATABASE	- имя базы данных
    - DB_USER		- логин пользователя
    - DB_PASSWORD	- пароль пользователя
    - DB_SCHEMA		- схема базы данных, в которой находится таблица, с которой должен работать endpoint
    - DB_TABLE		- наименование таблицы, с которой должен работать endpoint
Значения, содержащиеся в этом файле, задают конфигурацию, на которой выполнялось тестирование.

1.2. Запустить службы Docker: для Windows - запустить приложение Docker Desktop.
1.3. Выполнить сборку образа: для Windows - из консоли (cmd) перейти в папку /endpoint и выполнить команду: docker compose up --build
Образ готов к работе после отображения в консоли следующих сообщений:
	endpoint-1  |  * Running on all addresses (0.0.0.0)
	endpoint-1  |  * Running on http://127.0.0.1:5000
	endpoint-1  |  * Running on http://172.25.0.2:5000
	endpoint-1  | Press CTRL+C to quit


2. Тестирование решения проводилось с СУБД Postgres, развёрнутой в Docker-контейнере на локальном хосте.

2.1. Для развёртывания СУБД Postgres нужно выполнить следующие команды из консоли Windows (для успешного выполнения должно быть запущено приложение Docker Desktop):
	docker pull postgres
	docker volume create postgres_data
	docker run --name postgres_container -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 -v postgres_data:/var/lib/postgresql/data postgres
В результате на локальном хосте разворачивается экземпляр СУБД Postgres, который доступен по адресу http://localhost:5432, в нём создаётся база данных "postgres", к которой можно подключиться, используя следующие данные:
 	логин: postgres
 	пароль: mysecretpassword

2.2. Для начала работы необходимо создать в базе данных схему и таблицу, с которой будет работать endpoint. Название схемы и базы данных должно соответствовать переменным среды DB_SCHEMA и DB_TABLE, заданным в файле /endpoint/compose.yaml; в частности, для тестирования были созданы следующие объекты:

	create schema stats;

	create table stats.events
	(
		id bigint not null,
		event_date timestamp not null,
		attribute1 bigint null,
		attribute2 bigint null,
		attribute3 bigint null,
		attribute4 varchar null,
		attribute5 varchar null,
		attribute6 bool null,
		metric1 bigint not null,
		metric2 float8 not null
	);