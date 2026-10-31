// 自動生成: python -m jansen.cli scad （手で編集しないこと）
SCALE = 0.4;
THROWS = 3;
PLATE = 1.5;
WASHER = 0.3;
LINK_W = 7.0;
N_LAYERS = 5;
CENTER_WIDTH = 26.0;
SPACER_Y = 21.0;
L_a = 15.200;
L_b = 16.600;
L_c = 15.720;
L_d = 16.040;
L_e = 22.320;
L_f = 15.760;
L_g = 14.680;
L_h = 26.280;
L_i = 19.600;
L_j = 20.000;
L_k = 24.760;
L_l = 3.120;
L_m = 6.000;
// 機体の部品配置（機体座標: x 前, y 左, z 上。jansen/body.py）
CRANK_H = 36.73;
BRIDGE_X = [-41.00, 18.20]; BRIDGE_Y = [-12.50, 12.50]; BRIDGE_Z = [44.23, 64.23];
DECK_Z = [64.23, 65.23]; DECK_FRONT_X = [40.00, 64.00]; DECK_FRONT_Y = [-12.50, 12.50];
SENSOR_STANDOFFS = [[42.00, 9.00], [42.00, -9.00], [53.00, 10.50], [53.00, -10.50]];  // 壁センサ基板を吊るスペーサ (x, y)
SENSOR_BOARD_X = [40.00, 64.00]; SENSOR_BOARD_Y = [-12.50, 12.50]; SENSOR_BOARD_Z = [45.00, 45.80];
SENSORS = [[50.00, 5.00, 0.0], [50.00, -5.00, 0.0], [60.00, 13.00, 90.0], [60.00, -13.00, -90.0]];  // FL, FR, L, R: ホルダの前の面の真ん中 (x, y) と光の向き
HOLDER = [6.0, 4.04, 9.9, 7.6, 3.2];  // 幅, 奥行き, 高さ, 発光の穴, 受光の穴（基板の下面から）
MOTOR_X = [-34.00, 7.00]; MOTOR_Z = [29.73, 43.73];
DECK_X = [-40.00, 40.00]; DECK_Y = [-30.00, 30.00];
LAYER_T = 3;
LAYER_T_R = 1;
LAYER_U = 2;
LAYER_U_R = 3;
LAYER_c = 4;
LAYER_c_R = 4;
LAYER_f = 5;
LAYER_f_R = 5;
LAYER_j = 3;
LAYER_j_R = 4;
LAYER_k = 1;
LAYER_k_R = 2;
