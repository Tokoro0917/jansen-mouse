// 自動生成: python -m jansen.cli scad （手で編集しないこと）
SCALE = 0.45;
THROWS = 2;
PLATE = 2.0;
WASHER = 0.3;
LINK_W = 7.0;
N_LAYERS = 5;
CENTER_WIDTH = 26.0;
SPACER_Y = 25.0;
L_a = 17.100;
L_b = 18.675;
L_c = 17.685;
L_d = 18.045;
L_e = 25.110;
L_f = 17.730;
L_g = 16.515;
L_h = 29.565;
L_i = 22.050;
L_j = 22.500;
L_k = 27.855;
L_l = 3.510;
L_m = 6.750;
// 機体の部品配置（機体座標: x 前, y 左, z 上。jansen/body.py）
CRANK_H = 41.33;
CHASSIS_X = [-40.00, 40.00]; CHASSIS_Y = [-12.50, 12.50]; CHASSIS_Z = [48.83, 72.83];
FRONT_X = [40.00, 64.00]; FRONT_Z = [46.00, 72.83];
SENSOR_BOARD_X = [40.00, 64.00]; SENSOR_BOARD_Y = [-12.50, 12.50]; SENSOR_BOARD_Z = [45.00, 45.80];
SENSORS = [[50.00, 5.00, 0.0], [50.00, -5.00, 0.0], [60.00, 13.00, 90.0], [60.00, -13.00, -90.0]];  // FL, FR, L, R: ホルダの前の面の真ん中 (x, y) と光の向き
HOLDER = [6.0, 4.04, 9.9, 7.6, 3.2];  // 幅, 奥行き, 高さ, 発光の穴, 受光の穴（基板の下面から）
MOTOR_X = [-34.00, 7.00]; MOTOR_Z = [34.33, 48.33];
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
