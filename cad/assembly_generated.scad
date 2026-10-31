// 自動生成: python -m jansen.cli assembly （手で編集しないこと）
// 脚の平面 = XY（Y 上向き）、クランク軸 = Z。最後に全体を起こして Z 上向きにする。
include <parts.scad>
PART = "none";
rotate([90, 0, 0]) {
color("Gray") translate([0,0,-14.500]) frame();
color("DimGray") translate([0.000,0.000,-16.000]) rotate([0,0,30.000]) web();
color("DimGray") translate([0.000,0.000,-26.800]) rotate([0,0,30.000]) web();
color("SteelBlue") translate([5.196,3.000,-21.400]) rotate([0,0,149.425]) bar(L_j);
color("SteelBlue") translate([5.196,3.000,-23.200]) rotate([0,0,24.594]) bar(L_j);
color("SteelBlue") translate([5.196,3.000,-17.800]) rotate([0,0,-124.288]) bar(L_k);
color("SteelBlue") translate([5.196,3.000,-19.600]) rotate([0,0,-61.351]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,-23.200]) rotate([0,0,-65.786]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,-23.200]) rotate([0,0,-83.179]) bar(L_c);
color("SeaGreen") translate([-30.710,0.968,-25.000]) rotate([0,0,-58.955]) bar(L_f);
color("SeaGreen") translate([29.641,-10.101,-25.000]) rotate([0,0,-89.062]) bar(L_f);
color("Orange") translate([-15.200,-3.120,-19.600]) rotate([0,0,78.967]) tri_upper();
color("Orange") translate([15.200,-3.120,-21.400]) rotate([0,0,60.470]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-8.753,-17.457,-21.400]) rotate([0,0,160.409]) tri_foot();
color("Tomato") translate([17.067,-18.729,-17.800]) rotate([0,0,-29.057]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,-28.600]) frame();
color("DimGray") translate([0.000,0.000,-30.100]) rotate([0,0,150.000]) web();
color("DimGray") translate([0.000,0.000,-40.900]) rotate([0,0,150.000]) web();
color("SteelBlue") translate([-5.196,3.000,-35.500]) rotate([0,0,155.406]) bar(L_j);
color("SteelBlue") translate([-5.196,3.000,-37.300]) rotate([0,0,30.575]) bar(L_j);
color("SteelBlue") translate([-5.196,3.000,-31.900]) rotate([0,0,-118.649]) bar(L_k);
color("SteelBlue") translate([-5.196,3.000,-33.700]) rotate([0,0,-55.712]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,-37.300]) rotate([0,0,-96.821]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,-37.300]) rotate([0,0,-114.214]) bar(L_c);
color("SeaGreen") translate([-29.641,-10.101,-39.100]) rotate([0,0,-90.938]) bar(L_f);
color("SeaGreen") translate([30.710,0.968,-39.100]) rotate([0,0,-121.045]) bar(L_f);
color("Orange") translate([-15.200,-3.120,-33.700]) rotate([0,0,119.530]) tri_upper();
color("Orange") translate([15.200,-3.120,-35.500]) rotate([0,0,101.033]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-17.067,-18.729,-35.500]) rotate([0,0,-150.943]) tri_foot();
color("Tomato") translate([8.753,-17.457,-31.900]) rotate([0,0,19.591]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,-42.700]) frame();
color("DimGray") translate([0.000,0.000,-44.200]) rotate([0,0,-90.000]) web();
color("DimGray") translate([0.000,0.000,-55.000]) rotate([0,0,-90.000]) web();
color("SteelBlue") translate([-0.000,-6.000,-49.600]) rotate([0,0,115.276]) bar(L_j);
color("SteelBlue") translate([-0.000,-6.000,-51.400]) rotate([0,0,64.724]) bar(L_j);
color("SteelBlue") translate([-0.000,-6.000,-46.000]) rotate([0,0,-152.921]) bar(L_k);
color("SteelBlue") translate([-0.000,-6.000,-47.800]) rotate([0,0,-27.079]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,-51.400]) rotate([0,0,-115.816]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,-51.400]) rotate([0,0,-64.184]) bar(L_c);
color("SeaGreen") translate([-29.442,4.258,-53.200]) rotate([0,0,-110.862]) bar(L_f);
color("SeaGreen") translate([29.442,4.258,-53.200]) rotate([0,0,-69.138]) bar(L_f);
color("Orange") translate([-15.200,-3.120,-47.800]) rotate([0,0,66.345]) tri_upper();
color("Orange") translate([15.200,-3.120,-49.600]) rotate([0,0,113.655]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-22.046,-17.271,-49.600]) rotate([0,0,152.394]) tri_foot();
color("Tomato") translate([22.046,-17.271,-46.000]) rotate([0,0,27.606]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,-56.800]) frame();
color("Gray") translate([0,0,13.000]) frame();
color("DimGray") translate([0.000,0.000,14.500]) rotate([0,0,30.000]) web();
color("DimGray") translate([0.000,0.000,25.300]) rotate([0,0,30.000]) web();
color("SteelBlue") translate([5.196,3.000,19.900]) rotate([0,0,149.425]) bar(L_j);
color("SteelBlue") translate([5.196,3.000,21.700]) rotate([0,0,24.594]) bar(L_j);
color("SteelBlue") translate([5.196,3.000,16.300]) rotate([0,0,-124.288]) bar(L_k);
color("SteelBlue") translate([5.196,3.000,18.100]) rotate([0,0,-61.351]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,21.700]) rotate([0,0,-65.786]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,21.700]) rotate([0,0,-83.179]) bar(L_c);
color("SeaGreen") translate([-30.710,0.968,23.500]) rotate([0,0,-58.955]) bar(L_f);
color("SeaGreen") translate([29.641,-10.101,23.500]) rotate([0,0,-89.062]) bar(L_f);
color("Orange") translate([-15.200,-3.120,18.100]) rotate([0,0,78.967]) tri_upper();
color("Orange") translate([15.200,-3.120,19.900]) rotate([0,0,60.470]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-8.753,-17.457,19.900]) rotate([0,0,160.409]) tri_foot();
color("Tomato") translate([17.067,-18.729,16.300]) rotate([0,0,-29.057]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,27.100]) frame();
color("DimGray") translate([0.000,0.000,28.600]) rotate([0,0,150.000]) web();
color("DimGray") translate([0.000,0.000,39.400]) rotate([0,0,150.000]) web();
color("SteelBlue") translate([-5.196,3.000,34.000]) rotate([0,0,155.406]) bar(L_j);
color("SteelBlue") translate([-5.196,3.000,35.800]) rotate([0,0,30.575]) bar(L_j);
color("SteelBlue") translate([-5.196,3.000,30.400]) rotate([0,0,-118.649]) bar(L_k);
color("SteelBlue") translate([-5.196,3.000,32.200]) rotate([0,0,-55.712]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,35.800]) rotate([0,0,-96.821]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,35.800]) rotate([0,0,-114.214]) bar(L_c);
color("SeaGreen") translate([-29.641,-10.101,37.600]) rotate([0,0,-90.938]) bar(L_f);
color("SeaGreen") translate([30.710,0.968,37.600]) rotate([0,0,-121.045]) bar(L_f);
color("Orange") translate([-15.200,-3.120,32.200]) rotate([0,0,119.530]) tri_upper();
color("Orange") translate([15.200,-3.120,34.000]) rotate([0,0,101.033]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-17.067,-18.729,34.000]) rotate([0,0,-150.943]) tri_foot();
color("Tomato") translate([8.753,-17.457,30.400]) rotate([0,0,19.591]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,41.200]) frame();
color("DimGray") translate([0.000,0.000,42.700]) rotate([0,0,-90.000]) web();
color("DimGray") translate([0.000,0.000,53.500]) rotate([0,0,-90.000]) web();
color("SteelBlue") translate([-0.000,-6.000,48.100]) rotate([0,0,115.276]) bar(L_j);
color("SteelBlue") translate([-0.000,-6.000,49.900]) rotate([0,0,64.724]) bar(L_j);
color("SteelBlue") translate([-0.000,-6.000,44.500]) rotate([0,0,-152.921]) bar(L_k);
color("SteelBlue") translate([-0.000,-6.000,46.300]) rotate([0,0,-27.079]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,49.900]) rotate([0,0,-115.816]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,49.900]) rotate([0,0,-64.184]) bar(L_c);
color("SeaGreen") translate([-29.442,4.258,51.700]) rotate([0,0,-110.862]) bar(L_f);
color("SeaGreen") translate([29.442,4.258,51.700]) rotate([0,0,-69.138]) bar(L_f);
color("Orange") translate([-15.200,-3.120,46.300]) rotate([0,0,66.345]) tri_upper();
color("Orange") translate([15.200,-3.120,48.100]) rotate([0,0,113.655]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-22.046,-17.271,48.100]) rotate([0,0,152.394]) tri_foot();
color("Tomato") translate([22.046,-17.271,44.500]) rotate([0,0,27.606]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,55.300]) frame();
color("Black", 0.6) translate([-30,-10,-12.0]) cube([60, 30, 24.0]);  // 電装部
color("White", 0.3) translate([-90, -37.73, -90]) cube([180, 1, 180]);  // 床（1 区画分）
}
// 機体の部品（jansen/body.py の default_design）
color("LightSteelBlue") mirror([0, 1, 0]) translate([0, 0, -36.73]) { bridge(); motor_clamp(); standoffs(); }
color("Black") mirror([0, 1, 0]) translate([0, 0, -36.73]) placed_holders();
color("Silver") translate([-34.00, -12.50, -7.00]) cube([41.00, 12.00, 14.00]);  // motor_L
color("Silver") translate([-34.00, 0.50, -7.00]) cube([41.00, 12.00, 14.00]);  // motor_R
color("DarkGreen") translate([-40.00, -30.00, 27.50]) cube([80.00, 60.00, 1.00]);  // deck
color("DarkGreen") translate([40.00, -12.50, 27.50]) cube([24.00, 25.00, 1.00]);  // deck_front
color("Navy") translate([-26.00, -10.50, 28.50]) cube([53.00, 21.00, 4.00]);  // mcu
color("Gold") translate([-20.00, -31.00, 28.50]) cube([34.00, 18.00, 12.00]);  // battery
color("Purple") translate([-6.00, 16.00, 28.50]) cube([12.00, 12.00, 1.00]);  // imu
color("Maroon") translate([28.00, 16.00, 28.50]) cube([10.00, 12.00, 2.00]);  // driver
color("Teal") translate([40.00, -12.50, 8.27]) cube([24.00, 25.00, 0.80]);  // sensor_board
color("Red", 0.6) hull() { translate([50.00, -5.00, 2.87]) sphere(0.8, $fn=8); translate([84.00, -5.00, 2.87]) sphere(0.8, $fn=8); }  // 壁センサ FL の光路
color("Red", 0.6) hull() { translate([50.00, 5.00, 2.87]) sphere(0.8, $fn=8); translate([84.00, 5.00, 2.87]) sphere(0.8, $fn=8); }  // 壁センサ FR の光路
color("Red", 0.6) hull() { translate([60.00, -13.00, 2.87]) sphere(0.8, $fn=8); translate([60.00, -84.00, 2.87]) sphere(0.8, $fn=8); }  // 壁センサ L の光路
color("Red", 0.6) hull() { translate([60.00, 13.00, 2.87]) sphere(0.8, $fn=8); translate([60.00, 84.00, 2.87]) sphere(0.8, $fn=8); }  // 壁センサ R の光路
color("White", 0.25) translate([84, -90, -36.73]) cube([12, 180, 50]);  // 前壁（区画中心にいるとき）
