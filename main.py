from spacetrack_connector import DataExtractor as dt;
from orekit_setup import Scenario as sc;

# Definindo as restrições de pesquisa
constraints =[
    [dt.SearchFields.NORAD_CAT_ID, dt.Operators.EQUAL, 25544],                 # ID = 25544
    [dt.SearchFields.EPOCH, dt.Operators.RANGE, "2010-01-01", "2010-12-01"],   # 2010-01-01 <= época <= 2010-12-01
];

db = dt.SpaceTrackDatabases.HIST_RECORDS;   # Definindo o banco de dados que queremos (medições históricas)
file_name = "ISS_dados.json";               # Definindo o nome do arquivo que será criado (a extensão sempre será json)
order_by = dt.SearchFields.EPOCH;           # Definindo o campo pelo qual as entradas devem ser ordenadas (por época)

dt.SpaceTrackQuery(constraints, db, file_name, order_by);  # Fazendo a pesquisa

mass = 1000.0;  # massa em kg do objeto
area = 2.0;    # área transversal em m^2
cr = 1.2;      # Coeficiente de Reflexão (relevante para Pressão da Radiação Solar)

# O "cenário" contém todas as informações relevantes do problema:
# - Estado Inicial;
# - Propagador (Método usado para dizer a posição em um determinado tempo);
# - Forças a serem consideradas no modelo.
scenario1 = sc(mass, area, cr);
scenario1.BuildInitialState(file_name, entry = 0);   # Criando o Estado Inicial a partir da entrada 0 do arquivo json
scenario1.BuildBasicPropagator();                    # Iniciando o Propagador Numérico

# A partir daqui, devemos incluir as forças no modelo
scenario1.AddEarthGravity();            # Gravidade da Terra
scenario1.AddMoonGravity();             # Gravidade da Lua
# scenario1.AddSunGravity();              # Gravidade do Sol
# scenario1.AddSolarRadiationPressure();  # Pressão da Radiação Solar

print(scenario1);
target_date = scenario1.initial_state.getDate().shiftedBy(100.0);   # Tempo alvo 100s no futuro do Estado Inicial
final_state = scenario1.propagator.propagate(target_date);          # Propagando Estado Inicial

# Criando outro cenário pra imprimir o resultado
scenario2 = sc(mass, area, cr);
scenario2.initial_state = final_state;
print(scenario2);