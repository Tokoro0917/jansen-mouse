// 自動生成: python -m jansen.cli assembly （手で編集しないこと）
// 脚の平面 = XY（Y 上向き）、クランク軸 = Z。最後に全体を起こして Z 上向きにする。
include <parts.scad>
PART = "none";
rotate([90, 0, 0]) {
color("Gray") translate([0,0,-15.000]) frame();
color("DimGray") translate([0.000,0.000,-17.000]) rotate([0,0,30.000]) web();
color("DimGray") translate([0.000,0.000,-30.800]) rotate([0,0,30.000]) web();
color("SteelBlue") translate([5.846,3.375,-23.900]) rotate([0,0,149.425]) bar(L_j);
color("SteelBlue") translate([5.846,3.375,-26.200]) rotate([0,0,24.594]) bar(L_j);
color("SteelBlue") translate([5.846,3.375,-19.300]) rotate([0,0,-124.288]) bar(L_k);
color("SteelBlue") translate([5.846,3.375,-21.600]) rotate([0,0,-61.351]) bar(L_k);
color("SeaGreen") translate([-17.100,-3.510,-26.200]) rotate([0,0,-65.786]) bar(L_c);
color("SeaGreen") translate([17.100,-3.510,-26.200]) rotate([0,0,-83.179]) bar(L_c);
color("SeaGreen") translate([-34.549,1.089,-28.500]) rotate([0,0,-58.955]) bar(L_f);
color("SeaGreen") translate([33.346,-11.363,-28.500]) rotate([0,0,-89.062]) bar(L_f);
color("Orange") translate([-17.100,-3.510,-21.600]) rotate([0,0,78.967]) tri_upper();
color("Orange") translate([17.100,-3.510,-23.900]) rotate([0,0,60.470]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-9.847,-19.639,-23.900]) rotate([0,0,160.409]) tri_foot();
color("Tomato") translate([19.201,-21.070,-19.300]) rotate([0,0,-29.057]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,-33.100]) frame();
color("DimGray") translate([0.000,0.000,-35.100]) rotate([0,0,-150.000]) web();
color("DimGray") translate([0.000,0.000,-48.900]) rotate([0,0,-150.000]) web();
color("SteelBlue") translate([-5.846,-3.375,-42.000]) rotate([0,0,124.817]) bar(L_j);
color("SteelBlue") translate([-5.846,-3.375,-44.300]) rotate([0,0,48.177]) bar(L_j);
color("SteelBlue") translate([-5.846,-3.375,-37.400]) rotate([0,0,-159.476]) bar(L_k);
color("SteelBlue") translate([-5.846,-3.375,-39.700]) rotate([0,0,-39.606]) bar(L_k);
color("SeaGreen") translate([-17.100,-3.510,-44.300]) rotate([0,0,-147.005]) bar(L_c);
color("SeaGreen") translate([17.100,-3.510,-44.300]) rotate([0,0,-94.816]) bar(L_c);
color("SeaGreen") translate([-35.141,-3.875,-46.600]) rotate([0,0,-137.559]) bar(L_f);
color("SeaGreen") translate([32.898,5.211,-46.600]) rotate([0,0,-101.049]) bar(L_f);
color("Orange") translate([-17.100,-3.510,-39.700]) rotate([0,0,94.891]) tri_upper();
color("Orange") translate([17.100,-3.510,-42.000]) rotate([0,0,115.168]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-31.933,-13.141,-42.000]) rotate([0,0,-170.594]) tri_foot();
color("Tomato") translate([15.615,-21.133,-37.400]) rotate([0,0,32.782]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,-51.200]) frame();
color("Gray") translate([0,0,13.000]) frame();
color("DimGray") translate([0.000,0.000,15.000]) rotate([0,0,30.000]) web();
color("DimGray") translate([0.000,0.000,28.800]) rotate([0,0,30.000]) web();
color("SteelBlue") translate([5.846,3.375,21.900]) rotate([0,0,149.425]) bar(L_j);
color("SteelBlue") translate([5.846,3.375,24.200]) rotate([0,0,24.594]) bar(L_j);
color("SteelBlue") translate([5.846,3.375,17.300]) rotate([0,0,-124.288]) bar(L_k);
color("SteelBlue") translate([5.846,3.375,19.600]) rotate([0,0,-61.351]) bar(L_k);
color("SeaGreen") translate([-17.100,-3.510,24.200]) rotate([0,0,-65.786]) bar(L_c);
color("SeaGreen") translate([17.100,-3.510,24.200]) rotate([0,0,-83.179]) bar(L_c);
color("SeaGreen") translate([-34.549,1.089,26.500]) rotate([0,0,-58.955]) bar(L_f);
color("SeaGreen") translate([33.346,-11.363,26.500]) rotate([0,0,-89.062]) bar(L_f);
color("Orange") translate([-17.100,-3.510,19.600]) rotate([0,0,78.967]) tri_upper();
color("Orange") translate([17.100,-3.510,21.900]) rotate([0,0,60.470]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-9.847,-19.639,21.900]) rotate([0,0,160.409]) tri_foot();
color("Tomato") translate([19.201,-21.070,17.300]) rotate([0,0,-29.057]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,31.100]) frame();
color("DimGray") translate([0.000,0.000,33.100]) rotate([0,0,-150.000]) web();
color("DimGray") translate([0.000,0.000,46.900]) rotate([0,0,-150.000]) web();
color("SteelBlue") translate([-5.846,-3.375,40.000]) rotate([0,0,124.817]) bar(L_j);
color("SteelBlue") translate([-5.846,-3.375,42.300]) rotate([0,0,48.177]) bar(L_j);
color("SteelBlue") translate([-5.846,-3.375,35.400]) rotate([0,0,-159.476]) bar(L_k);
color("SteelBlue") translate([-5.846,-3.375,37.700]) rotate([0,0,-39.606]) bar(L_k);
color("SeaGreen") translate([-17.100,-3.510,42.300]) rotate([0,0,-147.005]) bar(L_c);
color("SeaGreen") translate([17.100,-3.510,42.300]) rotate([0,0,-94.816]) bar(L_c);
color("SeaGreen") translate([-35.141,-3.875,44.600]) rotate([0,0,-137.559]) bar(L_f);
color("SeaGreen") translate([32.898,5.211,44.600]) rotate([0,0,-101.049]) bar(L_f);
color("Orange") translate([-17.100,-3.510,37.700]) rotate([0,0,94.891]) tri_upper();
color("Orange") translate([17.100,-3.510,40.000]) rotate([0,0,115.168]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-31.933,-13.141,40.000]) rotate([0,0,-170.594]) tri_foot();
color("Tomato") translate([15.615,-21.133,35.400]) rotate([0,0,32.782]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,49.200]) frame();
color("Black", 0.6) translate([-30,-10,-12.0]) cube([60, 30, 24.0]);  // 電装部
color("White", 0.3) translate([-90, -42.33, -90]) cube([180, 1, 180]);  // 床（1 区画分）
}
// 機体の部品（jansen/body.py の default_design）
color("LightSteelBlue") mirror([0, 1, 0]) translate([0, 0, -41.33]) { chassis(); motor_clamp(); }
color("Black") mirror([0, 1, 0]) translate([0, 0, -41.33]) placed_holders();
color("Silver") translate([-34.00, -12.50, -7.00]) cube([41.00, 12.00, 14.00]);  // motor_L
color("Silver") translate([-34.00, 0.50, -7.00]) cube([41.00, 12.00, 14.00]);  // motor_R
color("DarkGreen") translate([-40.00, -30.00, 31.50]) cube([80.00, 60.00, 1.00]);  // deck
color("Navy") translate([-26.00, -10.50, 32.50]) cube([53.00, 21.00, 4.00]);  // mcu
color("Gold") translate([-20.00, -31.00, 32.50]) cube([34.00, 18.00, 12.00]);  // battery
color("Purple") translate([-6.00, 16.00, 32.50]) cube([12.00, 12.00, 1.00]);  // imu
color("Maroon") translate([28.00, 16.00, 32.50]) cube([10.00, 12.00, 2.00]);  // driver
color("Teal") translate([40.00, -12.50, 3.67]) cube([24.00, 25.00, 0.80]);  // sensor_board
color("Red", 0.6) hull() { translate([50.00, -5.00, -1.73]) sphere(0.8, $fn=8); translate([84.00, -5.00, -1.73]) sphere(0.8, $fn=8); }  // 壁センサ FL の光路
color("Red", 0.6) hull() { translate([50.00, 5.00, -1.73]) sphere(0.8, $fn=8); translate([84.00, 5.00, -1.73]) sphere(0.8, $fn=8); }  // 壁センサ FR の光路
color("Red", 0.6) hull() { translate([60.00, -13.00, -1.73]) sphere(0.8, $fn=8); translate([60.00, -84.00, -1.73]) sphere(0.8, $fn=8); }  // 壁センサ L の光路
color("Red", 0.6) hull() { translate([60.00, 13.00, -1.73]) sphere(0.8, $fn=8); translate([60.00, 84.00, -1.73]) sphere(0.8, $fn=8); }  // 壁センサ R の光路
color("White", 0.25) translate([84, -90, -41.33]) cube([12, 180, 50]);  // 前壁（区画中心にいるとき）
