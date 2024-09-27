from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from flasgger import Swagger
from flask_restx import Api, Resource, fields
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import secrets

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:4200"}})
socketio = SocketIO(app)

# Configuração Swagger
swagger = Swagger(app)

secrets_key = secrets.token_hex(32)
print(secrets_key)
app.config['SECRET_KEY'] = str(secrets_key)
# Inicializando a API RESTx
api = Api(app, version='1.0', title='Sistema de Gestão Escolar', description='Documentação com Swagger para a API da ACADEMICUM')

# Configurações do banco de dados PostgreSQL
DATABASE_URL = "dbname='academicum' user='postgres' password='postgres' host='localhost'"

# Função para conectar ao banco
def connect_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Definindo o modelo de usuário para o Swagger
user_model = api.model('User', {
    'nome_usuario': fields.String(required=True, description='Nome de usuário'),
    'email_usuario': fields.String(required=True, description='Email do usuário'),
    'telefone_usuario': fields.String(required=True, description='Telefone do usuário'),
    'senha_usuario': fields.String(required=True, description='Senha do usuário'),
    'tipo_usuario_id': fields.Integer(required=True, description='ID do tipo de usuário')
})

login_model = api.model('Login', {
    'email_usuario': fields.String(required=True, description='Email do usuário'),
    'senha_usuario': fields.String(required=True, description='Senha do usuário')
})
tipo_user_model = api.model('TipoUser', {
    'nome_tipo_usuario': fields.String(required=True, description='Nome do tipo de usuário')
})

departamento = api.model('Departamento', {
      'nome_departamento': fields.String(required=True, description='Nome do departamento'),
      'descricao': fields.String(requires=True, description='Descrição do departamento')
})

curso = api.model('Cursos', {
     'nome_curso': fields.String(required=True, description='Nome do curso'),
     'departamento_id': fields.Integer(required=True, description='ID do departamento')

})

periodo = api.model('Periodo', {
    'nome_periodo': fields.String(required=True, description='Nome do periodo')
})

turma = api.model('Turma', {
     'nome_turma': fields.String(required=True, description='Nome da Turma'),
     'periodo_id': fields.Integer(required=True, description='ID do período') 
})

aluno = api.model('Aluno', {
     'usuario_id': fields.Integer(required=True, description='ID do Usuário Aluno'),
     'curso_id': fields.Integer(required=True, description='ID do Curso'),
     'turma_id': fields.Integer(required=True, description='ID da Turma')
})

professor = api.model('Professor', {
     'usuario_id': fields.Integer(required=True, description='ID do Usuário Professor'),
     'departamento_id': fields.Integer(required=True, description='ID do Departamento')
})

disciplina = api.model('Disciplina', {
    'nome_disciplina': fields.String(required=True, description='Nome da disciplina'),
    'carga_horaria': fields.Integer(required=True, description='Carga horária da disciplina'),
    'curso_id': fields.Integer(required=True, description='ID do curso'),
    'professor_id': fields.Integer(required=True, description='ID do professor')
})


############################# Disciplina ##################################

@api.route('/disciplina')
class Disciplinas(Resource):
    @api.expect(disciplina)
    def post(self):
        """ Cria nova disciplina
        --- 
        responses:
          201:
             description: Disciplina criada com sucesso
          400:
             description: Erro nos dados fornecidos
          500:
            description: Erro no servidor              
        """

        data = request.json
        nome_disciplina = data['nome_disciplina']
        carga_horaria = data['carga_horaria']
        curso_id = data['curso_id']
        professor_id = data['professor_id']

        conn = connect_db()
        curu = conn.cursor()

        try:
            # Inserir dados no banco de dados Professor
            curu.execute(""" INSERT INTO disciplina (nome_disciplina, carga_horaria, curso_id, professor_id) VALUES (%s, %s, %s, %s) """, (nome_disciplina, carga_horaria, curso_id, professor_id))
            conn.commit()
            return {'message': 'Disciplina criada com sucesso!'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            curu.close()
            conn.close()

    def get(self):
        """ Lista todas Disciplinas 
         ---
        responses:
          200:
            description: Retorna a lista de Disciplinas
            """
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 
               SELECT
    disc.id_disciplina,
    disc.nome_disciplina,	 
    disc.carga_horaria,
    cur.nome_curso,
    u.nome_usuario  
FROM
    disciplina disc
INNER JOIN
    curso cur ON disc.curso_id = cur.id_curso 
INNER JOIN
    professor prof ON disc.professor_id = prof.id_professor
INNER JOIN
    usuario u ON prof.usuario_id = u.id_usuario; 
 
                """)
            tipousers = cur.fetchall()
            user_list = [{'id_disciplina': u[0], 'nome_disciplina': u[1], 'carga_horaria': u[2] , 'nome_curso': u[3], 'usuario_id': u[4]} for u in tipousers]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

@api.route('/disciplina/<int:id>')
class DisciplinaEdit(Resource):
    @api.expect(disciplina)
    def put(self, id_disciplina):
        """ Edita uma disciplina
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID do Aluno
        responses:
          200:
            description: Disciplina atualizado com sucesso
          400:
            description: Erro nos dados fornecidos
          500:
            description: Erro no servidor
        """
        data = request.json
        nome_curso = data['nome_curso']
         
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE curso
                SET nome_curso = %s 
                WHERE id_curso = %s
            """, (nome_curso, id_disciplina))
            conn.commit()
            if cur.rowcount == 0:
                return {'message': 'Curso não encontrado'}, 404
            return {'message': 'Curso atualizado com sucesso!'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()




############################# Fim da Disciplina ###########################



############################# Professores ##################################

@api.route('/professor')
class Professores(Resource):
    @api.expect(professor)
    def post(self):
        """ Cria novo professor
        --- 
        responses:
          201:
             description: Professor criado com sucesso
          400:
             description: Erro nos dados fornecidos
          500:
            description: Erro no servidor              
        """

        data = request.json
        usuario_id = data['usuario_id']
        departamento_id = data['departamento_id']
        conn = connect_db()
        curu = conn.cursor()

        try:
            # Inserir dados no banco de dados Professor
            curu.execute(""" INSERT INTO professor (usuario_id, departamento_id) VALUES (%s, %s) """, (usuario_id, departamento_id))
            conn.commit()
            return {'message': 'Professor criado com sucesso!'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            curu.close()
            conn.close()

    def get(self):
        """ Lista todos Professores
         ---
        responses:
          200:
            description: Retorna a lista de professores
            """
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 
               SELECT
                prof.id_professor,
                usua.nome_usuario,
                usua.email_usuario,
                usua.telefone_usuario,	
                depa.nome_departamento,
                prof.data_criacao	
                FROM
                professor prof
                INNER JOIN
                usuario usua
                ON prof.usuario_id = usua.id_usuario 
                INNER JOIN
                departamento depa
                ON prof.departamento_id = depa.id_departamento 
          """)
            tipousers = cur.fetchall()
            user_list = [{'id_professor': u[0], 'nome_usuario': u[1], 'email_usuario': u[2] , 'telefone_usuario': u[3], 'nome_departamento': u[4], 'data_criacao': u[5]} for u in tipousers]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

@api.route('/professor/<int:id>')
class ProfEdit(Resource):
    @api.expect(professor)
    def put(self, id_professor):
        """ Edita um aluno
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID do Aluno
        responses:
          200:
            description: Aluno atualizado com sucesso
          400:
            description: Erro nos dados fornecidos
          500:
            description: Erro no servidor
        """
        data = request.json
        nome_curso = data['nome_curso']
         
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE curso
                SET nome_curso = %s 
                WHERE id_curso = %s
            """, (nome_curso, id_professor))
            conn.commit()
            if cur.rowcount == 0:
                return {'message': 'Curso não encontrado'}, 404
            return {'message': 'Curso atualizado com sucesso!'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

############################ Fim Professores ################################


############################# ALUNOS ###############################

@api.route('/aluno')
class Alunos(Resource):
    @api.expect(aluno)
    def post(self):
        """ Cria novo aluno
        --- 
        responses:
          201:
             description: Aluno criado com sucesso
          400:
             description: Erro nos dados fornecidos
          500:
            description: Erro no servidor              
        """

        data = request.json
        
        usuario_id = data['usuario_id']
        curso_id = data['curso_id']
        turma_id = data['turma_id']
        conn = connect_db()
        curu = conn.cursor()
        
        try:
            # Inserir dados no banco de dados tipoUsuário
            curu.execute(""" INSERT INTO aluno (usuario_id, curso_id, turma_id) VALUES (%s, %s, %s) """, (usuario_id, curso_id , turma_id))
            conn.commit()
            print(data)
            return {'message': 'Aluno criado com sucesso!'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            curu.close()
            conn.close()

    def get(self):
        """ Lista todos cursos
         ---
        responses:
          200:
            description: Retorna a lista de alunos
            """
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 
               SELECT
                aluno.id_aluno,
                usua.nome_usuario,
                usua.email_usuario,
                usua.telefone_usuario,	
                cur.nome_curso,
                turm.nome_turma	,
                aluno.data_criacao	
                FROM
                aluno aluno
                INNER JOIN
                usuario usua
                ON aluno.usuario_id = usua.id_usuario 
                INNER JOIN
                curso cur
                ON aluno.curso_id = cur.id_curso
                INNER JOIN
                turma turm
                ON aluno.turma_id = turm.id_turma 
          """)
            tipousers = cur.fetchall()
            user_list = [{'id_aluno': u[0], 'nome_usuario': u[1], 'email_usuario': u[2] , 'telefone_usuario': u[3], 'nome_curso': u[4], 'nome_turma': u[5], 'data_criacao': u[6]} for u in tipousers]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

@api.route('/aluno/<int:id>')
class AlunoEdit(Resource):
    @api.expect(aluno)
    def put(self, id_aluno):
        """ Edita um aluno
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID do Aluno
        responses:
          200:
            description: Aluno atualizado com sucesso
          400:
            description: Erro nos dados fornecidos
          500:
            description: Erro no servidor
        """
        data = request.json
        nome_curso = data['nome_curso']
         
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE curso
                SET nome_curso = %s 
                WHERE id_curso = %s
            """, (nome_curso, id_aluno))
            conn.commit()
            if cur.rowcount == 0:
                return {'message': 'Curso não encontrado'}, 404
            return {'message': 'Curso atualizado com sucesso!'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

############################ FIM ALUNOS ############################


################################ Turmas ############################

@api.route('/turma')
class Turmas(Resource):
    @api.expect(turma)
    def post(self):
        """ Cria nova turma
        --- 
        responses:
          201:
             description: Turma criado com sucesso
          400:
             description: Erro nos dados fornecidos
          500:
            description: Erro no servidor              
        """

        data = request.json
        nome_turma = data['nome_turma']
        periodo_id = data['periodo_id']
        conn = connect_db()
        curu = conn.cursor()

        try:
            # Inserir dados no banco de dados tipoUsuário
            curu.execute(""" INSERT INTO turma (nome_turma, periodo_id) VALUES (%s, %s) """, (nome_turma, periodo_id))
            conn.commit()
            return {'message': 'Turma criado com sucesso!'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            curu.close()
            conn.close()

    def get(self):
        """ Lista todas Turmas
         ---
        responses:
          200:
            description: Retorna a lista de todas Turmas
            """
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 

            SELECT
            turmas.id_turma,
            turmas.nome_turma,
            perio.nome_periodo
            FROM
            turma turmas
            INNER JOIN
            periodo perio
            ON turmas.periodo_id = perio.id_periodo
            """)
            tipousers = cur.fetchall()
            user_list = [{'id_turma': u[0], 'nome_turma': u[1], 'nome_periodo': u[2]} for u in tipousers]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

@api.route('/curso/<int:id>')
class TipoUserEdit(Resource):
    @api.expect(tipo_user_model)
    def put(self, id_curso):
        """ Edita um curso
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID do curso
        responses:
          200:
            description: Curso atualizado com sucesso
          400:
            description: Erro nos dados fornecidos
          500:
            description: Erro no servidor
        """
        data = request.json
        nome_curso = data['nome_curso']
         
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE curso
                SET nome_curso = %s 
                WHERE id_curso = %s
            """, (nome_curso, id_curso))
            conn.commit()
            if cur.rowcount == 0:
                return {'message': 'Curso não encontrado'}, 404
            return {'message': 'Curso atualizado com sucesso!'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

############################### Fim Turmas #########################



################################# Periodo ###########################
@api.route('/periodo')
class Periodos(Resource):
    def get(self):
        """ Lista todos periodos
         ---
        responses:
          200:
            description: Retorna a lista de todos periodos
            """
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 
            SELECT
            id_periodo,
            nome_periodo,
            data_criacao
            FROM
            periodo
            """)
            periodo = cur.fetchall()
            user_list = [{'id_periodo': u[0], 'nome_periodo': u[1], 'data_criacao': u[2]} for u in periodo]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()


################################ Fim periodo ########################


################### Cursos #####################
@api.route('/cursos')
class Cursos(Resource):
    @api.expect(curso)
    def post(self):
        """ Cria novo curso
        --- 
        responses:
          201:
             description: Curso criado com sucesso
          400:
             description: Erro nos dados fornecidos
          500:
            description: Erro no servidor              
        """

        data = request.json
        nome_curso = data['nome_curso']
        departamento_id = data['departamento_id']
        conn = connect_db()
        curu = conn.cursor()

        try:
            # Inserir dados no banco de dados tipoUsuário
            curu.execute(""" INSERT INTO curso (nome_curso, departamento_id) VALUES (%s, %s) """, (nome_curso, departamento_id))
            conn.commit()
            return {'message': 'Curso criado com sucesso!'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            curu.close()
            conn.close()

    def get(self):
        """ Lista todos cursos
         ---
        responses:
          200:
            description: Retorna a lista de cursos
            """
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 

            SELECT
            cursos.id_curso,
            cursos.nome_curso,
            depa.nome_departamento
            FROM
            curso cursos
            INNER JOIN
            departamento depa
            ON cursos.departamento_id = depa.id_departamento
            """)
            tipousers = cur.fetchall()
            user_list = [{'id_curso': u[0], 'nome_curso': u[1], 'nome_departamento': u[2]} for u in tipousers]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

@api.route('/curso/<int:id>')
class TipoUserEdit(Resource):
    @api.expect(tipo_user_model)
    def put(self, id_curso):
        """ Edita um curso
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID do curso
        responses:
          200:
            description: Curso atualizado com sucesso
          400:
            description: Erro nos dados fornecidos
          500:
            description: Erro no servidor
        """
        data = request.json
        nome_curso = data['nome_curso']
         
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE curso
                SET nome_curso = %s 
                WHERE id_curso = %s
            """, (nome_curso, id_curso))
            conn.commit()
            if cur.rowcount == 0:
                return {'message': 'Curso não encontrado'}, 404
            return {'message': 'Curso atualizado com sucesso!'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()


################## Fim cursos ##################


@api.route('/alunos/somente')
class CreateUser(Resource):

    def get(self):
        """Lista somente alunos
        ---
        responses:
          200:
            description: Retorna a lista de usuários
        """
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 
 SELECT
usua.id_usuario,
usua.nome_usuario,
usua.email_usuario,
usua.telefone_usuario,
tipo.nome_tipo_usuario
FROM
usuario usua
INNER JOIN
tipo_usuario tipo ON 
usua.tipo_usuario_id = tipo.id_tipo_usuario
WHERE 
usua.tipo_usuario_id = 1
           
    """)
            users = cur.fetchall()
            user_list = [{'id_aluno': u[0], 'nome_usuario': u[1], 'email_usuario': u[2], 'telefone_usuario': u[3]} for u in users]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

@api.route('/professores/somente')
class Profes(Resource):

    def get(self):
        """Lista somente professores
        ---
        responses:
          200:
            description: Retorna a lista de professores
        """
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 
        SELECT
        prof.id_professor,
        usua.nome_usuario
        FROM
        professor prof
        INNER JOIN
        usuario usua
        ON prof.usuario_id = usua.id_usuario
        WHERE
        usua.tipo_usuario_id = 2;           
    """)
            users = cur.fetchall()
            user_list = [{'id_professor': u[0], 'nome_usuario': u[1]} for u in users]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

################### Departamento ###############

@api.route('/departamento')
class Departamento(Resource):
    @api.expect(departamento)
    def post(self):
        """ Cria novo departamento
        --- 
        responses:
          201:
             description: Tipo de usuário criado com sucesso
          400:
             description: Erro nos dados fornecidos
          500:
            description: Erro no servidor              
        """

        data = request.json
        nome_departamento = data['nome_departamento']
        descricao = data['descricao']
        conn = connect_db()
        curu = conn.cursor()

        try:
            # Inserir dados no banco de dados tipoUsuário
            curu.execute(""" INSERT INTO departamento (nome_departamento, descricao) VALUES (%s, %s) """, (nome_departamento, descricao))
            conn.commit()
            return {'message': 'Departamento criado com sucesso!'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            curu.close()
            conn.close()

    def get(self):
        """ Lista todos departamentos
         ---
        responses:
          200:
            description: Retorna a lista de departamentos
            """
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 

            SELECT
            id_departamento,
            nome_departamento,
            descricao
            FROM
            departamento
            """)
            tipousers = cur.fetchall()
            user_list = [{'id_departamento': u[0], 'nome_departamento': u[1], 'descricao': u[2]} for u in tipousers]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

####################### Fim Depa ############################################

@api.route('/tipoUsuario')
class TipoUsers(Resource):
    @api.expect(tipo_user_model)
    def post(self):
        """ Cria novo tipo de usuário
        --- 
        responses:
          201:
             description: Tipo de usuário criado com sucesso
          400:
             description: Erro nos dados fornecidos
          500:
            description: Erro no servidor              
        """

        data = request.json
        nome_tipo_usuario = data['nome_tipo_usuario']
        conn = connect_db()
        curu = conn.cursor()

        try:
            # Inserir dados no banco de dados tipoUsuário
            curu.execute(""" INSERT INTO tipo_usuario (nome_tipo_usuario) VALUES (%s) """,(nome_tipo_usuario,))
            conn.commit()
            return {'message': 'Tipo de Usuário criado com sucesso!'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            curu.close()
            conn.close()

    def get(self):
        """ Lista todos tipos de usuários
         ---
        responses:
          200:
            description: Retorna a lista de Tipo de usuários
            """
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 

            SELECT
            id_tipo_usuario,
            nome_tipo_usuario
            FROM
            tipo_usuario
            """)
            tipousers = cur.fetchall()
            user_list = [{'id_tipo_usuario': u[0], 'nome_tipo_usuario': u[1]} for u in tipousers]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()


@api.route('/tipoUsuario/<int:id>')
class TipoUserEdit(Resource):
    @api.expect(tipo_user_model)
    def put(self, id):
        """ Edita um tipo de usuário
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID do tipo de usuário
        responses:
          200:
            description: Tipo de usuário atualizado com sucesso
          400:
            description: Erro nos dados fornecidos
          500:
            description: Erro no servidor
        """
        data = request.json
        nome_tipo_usuario = data['nome_tipo_usuario']
        
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE tipo_usuario 
                SET nome_tipo_usuario = %s 
                WHERE id_tipo_usuario = %s
            """, (nome_tipo_usuario, id))
            conn.commit()
            if cur.rowcount == 0:
                return {'message': 'Tipo de Usuário não encontrado'}, 404
            return {'message': 'Tipo de Usuário atualizado com sucesso!'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

# Rota para criar um usuário
@api.route('/usuarios')
class CreateUser(Resource):
    @api.expect(user_model)
    def post(self):
        """Cria um novo usuário
        ---
        responses:
          201:
            description: Usuário criado com sucesso
          400:
            description: Erro nos dados fornecidos
          500:
            description: Erro no servidor
        """
        data = request.json
        nome_usuario = data['nome_usuario']
        email_usuario = data['email_usuario']
        telefone_usuario = data['telefone_usuario']
        senha_usuario = data['senha_usuario']
        tipo_usuario_id = data['tipo_usuario_id']

        hashed_password = generate_password_hash(senha_usuario)

        conn = connect_db()
        cur = conn.cursor()

        try:
            # Inserir dados do usuário no banco
            cur.execute("""
                INSERT INTO usuario (nome_usuario, email_usuario, telefone_usuario, senha_usuario, tipo_usuario_id) 
                VALUES (%s, %s, %s, %s, %s)
            """, (nome_usuario, email_usuario, telefone_usuario, hashed_password, tipo_usuario_id))
            conn.commit()
            return {'message': 'Usuário criado com sucesso!'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

    def get(self):
        """Lista todos os usuários
        ---
        responses:
          200:
            description: Retorna a lista de usuários
        """
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(""" 
 SELECT 
usu.id_usuario, 
usu.nome_usuario, 
usu.email_usuario, 
usu.telefone_usuario,
tipo.nome_tipo_usuario,
usu.data_criacao            
FROM 
usuario usu
INNER JOIN 
tipo_usuario tipo
ON usu.tipo_usuario_id = tipo.id_tipo_usuario
ORDER BY usu.id_usuario
            """)
            users = cur.fetchall()
            user_list = [{'id_usuario': u[0], 'nome_usuario': u[1], 'email_usuario': u[2], 'telefone_usuario': u[3], 'nome_tipo_usuario': u[4], 'data_criacao': u[5]} for u in users]
            return jsonify(user_list)
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

# Rota para deletar um usuário
@api.route('/usuarios/<int:id>')
class DeleteUser(Resource):
    def delete(self, id):
        """Deleta um usuário por ID
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID do usuário
        responses:
          200:
            description: Usuário deletado com sucesso
          404:
            description: Usuário não encontrado
        """
        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("DELETE FROM users WHERE id = %s", (id,))
            conn.commit()
            if cur.rowcount == 0:
                return {'message': 'Usuário não encontrado'}, 404
            return {'message': 'Usuário deletado com sucesso'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()
    def put(self, id):
        """ Edita um usuário
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
            description: ID do usuário
        responses:
          200:
            description: Usuário atualizado com sucesso
          404:
            description: Usuário não encontrado
          500:
            description: Erro no servidor
        """
        data = request.json
        nome_usuario = data['nome_usuario']
        email_usuario = data['email_usuario']
        telefone_usuario = data['telefone_usuario']
        senha_usuario = data['senha_usuario']
        tipo_usuario_id = data['tipo_usuario_id']
        
        hashed_password = generate_password_hash(senha_usuario)

        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE usuario 
                SET nome_usuario = %s, email_usuario = %s, telefone_usuario = %s, senha_usuario = %s, tipo_usuario_id = %s
                WHERE id_usuario = %s
            """, (nome_usuario, email_usuario, telefone_usuario, hashed_password, tipo_usuario_id, id))
            conn.commit()
            if cur.rowcount == 0:
                return {'message': 'Usuário não encontrado'}, 404
            return {'message': 'Usuário atualizado com sucesso!'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

# Rota para efetuar login
@api.route('/login')
class Login(Resource):
    @api.expect(login_model)
    def post(self):
        """Efetua o login de um usuário
        ---
        responses:
          200:
            description: Login bem-sucedido
          400:
            description: Usuário ou senha incorretos
        """
        data = request.json
        email_usuario = data.get('email_usuario')
        senha_usuario = data.get('senha_usuario')

        conn = connect_db()
        cur = conn.cursor()

        try:
            # Verifica se o usuário existe e faz o inner join para obter o nome do tipo de usuário
            cur.execute("""
                SELECT u.id_usuario, u.nome_usuario, u.email_usuario, u.senha_usuario, u.tipo_usuario_id, t.nome_tipo_usuario
                FROM usuario u
                INNER JOIN tipo_usuario t ON u.tipo_usuario_id = t.id_tipo_usuario
                WHERE u.email_usuario = %s
            """, (email_usuario,))
            
            user = cur.fetchone()

            if user and check_password_hash(user[3], senha_usuario):
                # Gerar token JWT
                token = jwt.encode({
                    'user_id': user[0],
                    'tipo_usuario_id': user[4],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # expira em 1 hora
                }, app.config['SECRET_KEY'], algorithm='HS256')

                return {
                    'message': 'Login bem-sucedido!',
                    'user_id': user[0],
                    'nome_usuario': user[1],
                    'email_usuario': user[2],
                    'nome_tipo_usuario': user[5],  # Inclui o nome do tipo de usuário
                    'token': token
                }, 200
            else:
                return {'message': 'Usuário ou senha incorretos'}, 400
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
        finally:
            cur.close()
            conn.close()

 ########################## Endpoints para o Departamento #####################



if __name__ == '__main__':
    socketio.run(app, debug=True)
