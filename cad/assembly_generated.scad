// 自動生成: python -m jansen.cli assembly （手で編集しないこと）
// 脚の平面 = XY（Y 上向き）、クランク軸 = Z。最後に全体を起こして Z 上向きにする。
include <parts.scad>
PART = "none";
rotate([90, 0, 0]) {
color("Gray") translate([0,0,-14.500]) frame();
color("DimGray") translate([0.000,0.000,-16.300]) rotate([0,0,30.000]) web();
color("DimGray") translate([0.000,0.000,-27.100]) rotate([0,0,30.000]) web();
color("SteelBlue") translate([5.196,3.000,-21.700]) rotate([0,0,149.425]) bar(L_j);
color("SteelBlue") translate([5.196,3.000,-23.500]) rotate([0,0,24.594]) bar(L_j);
color("SteelBlue") translate([5.196,3.000,-18.100]) rotate([0,0,-124.288]) bar(L_k);
color("SteelBlue") translate([5.196,3.000,-19.900]) rotate([0,0,-61.351]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,-23.500]) rotate([0,0,-65.786]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,-23.500]) rotate([0,0,-83.179]) bar(L_c);
color("SeaGreen") translate([-30.710,0.968,-25.300]) rotate([0,0,-58.955]) bar(L_f);
color("SeaGreen") translate([29.641,-10.101,-25.300]) rotate([0,0,-89.062]) bar(L_f);
color("Orange") translate([-15.200,-3.120,-19.900]) rotate([0,0,78.967]) tri_upper();
color("Orange") translate([15.200,-3.120,-21.700]) rotate([0,0,60.470]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-8.753,-17.457,-21.700]) rotate([0,0,160.409]) tri_foot();
color("Tomato") translate([17.067,-18.729,-18.100]) rotate([0,0,-29.057]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,-28.900]) frame();
color("DimGray") translate([0.000,0.000,-30.700]) rotate([0,0,150.000]) web();
color("DimGray") translate([0.000,0.000,-41.500]) rotate([0,0,150.000]) web();
color("SteelBlue") translate([-5.196,3.000,-36.100]) rotate([0,0,155.406]) bar(L_j);
color("SteelBlue") translate([-5.196,3.000,-37.900]) rotate([0,0,30.575]) bar(L_j);
color("SteelBlue") translate([-5.196,3.000,-32.500]) rotate([0,0,-118.649]) bar(L_k);
color("SteelBlue") translate([-5.196,3.000,-34.300]) rotate([0,0,-55.712]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,-37.900]) rotate([0,0,-96.821]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,-37.900]) rotate([0,0,-114.214]) bar(L_c);
color("SeaGreen") translate([-29.641,-10.101,-39.700]) rotate([0,0,-90.938]) bar(L_f);
color("SeaGreen") translate([30.710,0.968,-39.700]) rotate([0,0,-121.045]) bar(L_f);
color("Orange") translate([-15.200,-3.120,-34.300]) rotate([0,0,119.530]) tri_upper();
color("Orange") translate([15.200,-3.120,-36.100]) rotate([0,0,101.033]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-17.067,-18.729,-36.100]) rotate([0,0,-150.943]) tri_foot();
color("Tomato") translate([8.753,-17.457,-32.500]) rotate([0,0,19.591]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,-43.300]) frame();
color("DimGray") translate([0.000,0.000,-45.100]) rotate([0,0,-90.000]) web();
color("DimGray") translate([0.000,0.000,-55.900]) rotate([0,0,-90.000]) web();
color("SteelBlue") translate([-0.000,-6.000,-50.500]) rotate([0,0,115.276]) bar(L_j);
color("SteelBlue") translate([-0.000,-6.000,-52.300]) rotate([0,0,64.724]) bar(L_j);
color("SteelBlue") translate([-0.000,-6.000,-46.900]) rotate([0,0,-152.921]) bar(L_k);
color("SteelBlue") translate([-0.000,-6.000,-48.700]) rotate([0,0,-27.079]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,-52.300]) rotate([0,0,-115.816]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,-52.300]) rotate([0,0,-64.184]) bar(L_c);
color("SeaGreen") translate([-29.442,4.258,-54.100]) rotate([0,0,-110.862]) bar(L_f);
color("SeaGreen") translate([29.442,4.258,-54.100]) rotate([0,0,-69.138]) bar(L_f);
color("Orange") translate([-15.200,-3.120,-48.700]) rotate([0,0,66.345]) tri_upper();
color("Orange") translate([15.200,-3.120,-50.500]) rotate([0,0,113.655]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-22.046,-17.271,-50.500]) rotate([0,0,152.394]) tri_foot();
color("Tomato") translate([22.046,-17.271,-46.900]) rotate([0,0,27.606]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,-57.700]) frame();
color("Gray") translate([0,0,13.000]) frame();
color("DimGray") translate([0.000,0.000,14.800]) rotate([0,0,30.000]) web();
color("DimGray") translate([0.000,0.000,25.600]) rotate([0,0,30.000]) web();
color("SteelBlue") translate([5.196,3.000,20.200]) rotate([0,0,149.425]) bar(L_j);
color("SteelBlue") translate([5.196,3.000,22.000]) rotate([0,0,24.594]) bar(L_j);
color("SteelBlue") translate([5.196,3.000,16.600]) rotate([0,0,-124.288]) bar(L_k);
color("SteelBlue") translate([5.196,3.000,18.400]) rotate([0,0,-61.351]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,22.000]) rotate([0,0,-65.786]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,22.000]) rotate([0,0,-83.179]) bar(L_c);
color("SeaGreen") translate([-30.710,0.968,23.800]) rotate([0,0,-58.955]) bar(L_f);
color("SeaGreen") translate([29.641,-10.101,23.800]) rotate([0,0,-89.062]) bar(L_f);
color("Orange") translate([-15.200,-3.120,18.400]) rotate([0,0,78.967]) tri_upper();
color("Orange") translate([15.200,-3.120,20.200]) rotate([0,0,60.470]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-8.753,-17.457,20.200]) rotate([0,0,160.409]) tri_foot();
color("Tomato") translate([17.067,-18.729,16.600]) rotate([0,0,-29.057]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,27.400]) frame();
color("DimGray") translate([0.000,0.000,29.200]) rotate([0,0,150.000]) web();
color("DimGray") translate([0.000,0.000,40.000]) rotate([0,0,150.000]) web();
color("SteelBlue") translate([-5.196,3.000,34.600]) rotate([0,0,155.406]) bar(L_j);
color("SteelBlue") translate([-5.196,3.000,36.400]) rotate([0,0,30.575]) bar(L_j);
color("SteelBlue") translate([-5.196,3.000,31.000]) rotate([0,0,-118.649]) bar(L_k);
color("SteelBlue") translate([-5.196,3.000,32.800]) rotate([0,0,-55.712]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,36.400]) rotate([0,0,-96.821]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,36.400]) rotate([0,0,-114.214]) bar(L_c);
color("SeaGreen") translate([-29.641,-10.101,38.200]) rotate([0,0,-90.938]) bar(L_f);
color("SeaGreen") translate([30.710,0.968,38.200]) rotate([0,0,-121.045]) bar(L_f);
color("Orange") translate([-15.200,-3.120,32.800]) rotate([0,0,119.530]) tri_upper();
color("Orange") translate([15.200,-3.120,34.600]) rotate([0,0,101.033]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-17.067,-18.729,34.600]) rotate([0,0,-150.943]) tri_foot();
color("Tomato") translate([8.753,-17.457,31.000]) rotate([0,0,19.591]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,41.800]) frame();
color("DimGray") translate([0.000,0.000,43.600]) rotate([0,0,-90.000]) web();
color("DimGray") translate([0.000,0.000,54.400]) rotate([0,0,-90.000]) web();
color("SteelBlue") translate([-0.000,-6.000,49.000]) rotate([0,0,115.276]) bar(L_j);
color("SteelBlue") translate([-0.000,-6.000,50.800]) rotate([0,0,64.724]) bar(L_j);
color("SteelBlue") translate([-0.000,-6.000,45.400]) rotate([0,0,-152.921]) bar(L_k);
color("SteelBlue") translate([-0.000,-6.000,47.200]) rotate([0,0,-27.079]) bar(L_k);
color("SeaGreen") translate([-15.200,-3.120,50.800]) rotate([0,0,-115.816]) bar(L_c);
color("SeaGreen") translate([15.200,-3.120,50.800]) rotate([0,0,-64.184]) bar(L_c);
color("SeaGreen") translate([-29.442,4.258,52.600]) rotate([0,0,-110.862]) bar(L_f);
color("SeaGreen") translate([29.442,4.258,52.600]) rotate([0,0,-69.138]) bar(L_f);
color("Orange") translate([-15.200,-3.120,47.200]) rotate([0,0,66.345]) tri_upper();
color("Orange") translate([15.200,-3.120,49.000]) rotate([0,0,113.655]) mirror([0,1,0]) tri_upper();
color("Tomato") translate([-22.046,-17.271,49.000]) rotate([0,0,152.394]) tri_foot();
color("Tomato") translate([22.046,-17.271,45.400]) rotate([0,0,27.606]) mirror([0,1,0]) tri_foot();
color("Gray") translate([0,0,56.200]) frame();
color("Black", 0.6) translate([-30,-10,-12.0]) cube([60, 30, 24.0]);  // 電装部
color("White", 0.3) translate([-90, -37.73, -90]) cube([180, 1, 180]);  // 床（1 区画分）
}
// 機体の部品（jansen/body.py の default_design）
color("LightSteelBlue") mirror([0, 1, 0]) translate([0, 0, -36.73]) { bridge(); motor_clamp(); }
color("Black") mirror([0, 1, 0]) translate([0, 0, -36.73]) placed_holders();
color("Silver") translate([-34.00, -12.50, -7.00]) cube([41.00, 12.00, 14.00]);  // motor_L
color("Silver") translate([-34.00, 0.50, -7.00]) cube([41.00, 12.00, 14.00]);  // motor_R
color("DarkGreen") translate([-40.00, -30.00, 27.50]) cube([80.00, 60.00, 1.00]);  // deck
color("Navy") translate([-13.00, -30.00, 28.50]) cube([53.00, 21.00, 4.00]);  // mcu
color("Purple") translate([27.00, 18.00, 28.50]) cube([10.00, 10.00, 1.00]);  // imu
color("Maroon") translate([15.00, 18.00, 28.50]) cube([10.00, 10.00, 2.00]);  // driver
color("Gold") translate([5.64, -5.79, 28.50]) cube([34.00, 18.00, 12.00]);  // battery
color("Red", 0.6) hull() { translate([34.00, -9.00, 5.27]) sphere(0.8, $fn=8); translate([84.00, -9.00, 5.27]) sphere(0.8, $fn=8); }  // 壁センサ FL の光路
color("Red", 0.6) hull() { translate([34.00, 9.00, 5.27]) sphere(0.8, $fn=8); translate([84.00, 9.00, 5.27]) sphere(0.8, $fn=8); }  // 壁センサ FR の光路
color("Red", 0.6) hull() { translate([37.00, -5.00, 5.27]) sphere(0.8, $fn=8); translate([58.17, -84.00, 5.27]) sphere(0.8, $fn=8); }  // 壁センサ L の光路
color("Red", 0.6) hull() { translate([37.00, 5.00, 5.27]) sphere(0.8, $fn=8); translate([58.17, 84.00, 5.27]) sphere(0.8, $fn=8); }  // 壁センサ R の光路
color("White", 0.25) translate([84, -90, -36.73]) cube([12, 180, 50]);  // 前壁（区画中心にいるとき）
