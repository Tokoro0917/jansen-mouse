// 自動生成: python -m jansen.cli kit -o ../cad/print_kit_generated.scad （手で編集しないこと）
// 買う部品を減らした試作キット（jansen/print_kit.py）。PART = 部品名 で 1 つずつ書き出す。
PART = "all";
FDM_CLEAR = 0.2;   // FDM で穴を大きくする分
T = 1.5;
PIN_HOLE = 1.9 + FDM_CLEAR;
BOSS_D = 4.0;
HEX_HOLE_AF = 3.15 + FDM_CLEAR;
HEX_AF = 3.0;
JOURNAL = 3.8 + FDM_CLEAR;
TIE_HOLE = 2.2 + FDM_CLEAR;
POST_D = 4.0;
$fn = 40;
module hexagon(af) { circle(d = af / cos(30), $fn = 6); }
module hole(k) {
  if (k == "pin") circle(d = PIN_HOLE);
  if (k == "hex") hexagon(HEX_HOLE_AF);
  if (k == "journal") circle(d = JOURNAL);
  if (k == "tie") circle(d = TIE_HOLE);
}
module kit_j_front() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([-15.605,12.509]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 0.20);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([-15.605,12.509]) hole("pin"); }
  }
}
module kit_j_back() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([15.974,12.035]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 2.00);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([15.974,12.035]) hole("pin"); }
  }
}
module kit_k_front() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([-16.781,-18.206]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 0.20);
      translate([-16.781,-18.206,T]) cylinder(d = BOSS_D, h = 2.00);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([-16.781,-18.206]) hole("pin"); }
  }
}
module kit_k_back() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([20.126,-14.422]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 0.20);
      translate([20.126,-14.422,T]) cylinder(d = BOSS_D, h = 2.00);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([20.126,-14.422]) hole("pin"); }
  }
}
module kit_c_front() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([4.419,-15.086]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 3.80);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([4.419,-15.086]) hole("pin"); }
  }
}
module kit_c_back() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([10.926,-11.302]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 3.80);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([10.926,-11.302]) hole("pin"); }
  }
}
module kit_f_front() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([6.225,-14.478]) circle(d = 7.0); }
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([6.225,-14.478]) hole("pin"); }
  }
}
module kit_f_back() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([8.465,-13.294]) circle(d = 7.0); }
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([8.465,-13.294]) hole("pin"); }
  }
}
module kit_U_front() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([5.595,15.629]) circle(d = 7.0); translate([-14.718,6.377]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 2.00);
      translate([5.595,15.629,T]) cylinder(d = BOSS_D, h = 0.20);
      translate([-14.718,6.377,T]) cylinder(d = BOSS_D, h = 3.80);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([5.595,15.629]) hole("pin"); translate([-14.718,6.377]) hole("pin"); }
  }
}
module kit_U_back() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([6.774,15.155]) circle(d = 7.0); translate([15.039,-5.578]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 0.20);
      translate([6.774,15.155,T]) cylinder(d = BOSS_D, h = 0.20);
      translate([15.039,-5.578,T]) cylinder(d = BOSS_D, h = 2.00);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([6.774,15.155]) hole("pin"); translate([15.039,-5.578]) hole("pin"); }
  }
}
module kit_T_front() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([-12.912,6.985]) circle(d = 7.0); translate([-6.483,-18.497]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 0.20);
      translate([-12.912,6.985,T]) cylinder(d = BOSS_D, h = 2.00);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([-12.912,6.985]) hole("pin"); }
  }
}
module kit_T_back() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 7.0); translate([12.578,-7.569]) circle(d = 7.0); translate([-12.634,-14.985]) circle(d = 7.0); }
      translate([0.000,0.000,T]) cylinder(d = BOSS_D, h = 0.20);
      translate([12.578,-7.569,T]) cylinder(d = BOSS_D, h = 5.60);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("pin"); translate([12.578,-7.569]) hole("pin"); }
  }
}
module kit_web_inner() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 9.0); translate([6.000,0.000]) circle(d = 7.0); }
      translate([6.000,0.000,T]) cylinder(d = BOSS_D, h = 0.20);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("hex"); translate([6.000,0.000]) hole("pin"); }
  }
}
module kit_web_outer() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 9.0); translate([6.000,0.000]) circle(d = 7.0); }
      translate([0.000,0.000,T]) linear_extrude(3.60) hexagon(HEX_AF);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([6.000,0.000]) hole("pin"); }
  }
}
module kit_frame_outer() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([-15.200,-3.120]) circle(d = 9.0); translate([15.200,-3.120]) circle(d = 9.0); translate([0.000,0.000]) circle(d = 11.0); translate([-15.200,21.000]) circle(d = 7); translate([15.200,21.000]) circle(d = 7); }
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("journal"); translate([-15.200,-3.120]) hole("pin"); translate([15.200,-3.120]) hole("pin"); translate([-15.200,21.000]) hole("tie"); translate([15.200,21.000]) hole("tie"); }
  }
}
module kit_frame_inner() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([-15.200,-3.120]) circle(d = 9.0); translate([15.200,-3.120]) circle(d = 9.0); translate([0.000,0.000]) circle(d = 11.0); translate([-15.200,21.000]) circle(d = 7); translate([15.200,21.000]) circle(d = 7); }
      translate([-15.200,21.000,T]) cylinder(d = POST_D, h = 12.90);
      translate([-15.200,21.000,T + 12.90]) cylinder(d = TIE_HOLE - 0.3, h = 1.30);
      translate([15.200,21.000,T]) cylinder(d = POST_D, h = 12.90);
      translate([15.200,21.000,T + 12.90]) cylinder(d = TIE_HOLE - 0.3, h = 1.30);
    }
    translate([0,0,-1]) linear_extrude(50) { translate([0.000,0.000]) hole("journal"); translate([-15.200,-3.120]) hole("pin"); translate([15.200,-3.120]) hole("pin"); }
  }
}
module kit_hex_axle() {
  difference() {
    union() {
      linear_extrude(T) hull() { translate([0.000,0.000]) circle(d = 10); }
      translate([0.000,0.000,T]) linear_extrude(3.30) hexagon(HEX_AF);
    }
  }
}
// 1 モジュール分を並べて置く（PART = "all"）
if (PART == "j_front") kit_j_front();
if (PART == "j_back") kit_j_back();
if (PART == "k_front") kit_k_front();
if (PART == "k_back") kit_k_back();
if (PART == "c_front") kit_c_front();
if (PART == "c_back") kit_c_back();
if (PART == "f_front") kit_f_front();
if (PART == "f_back") kit_f_back();
if (PART == "U_front") kit_U_front();
if (PART == "U_back") kit_U_back();
if (PART == "T_front") kit_T_front();
if (PART == "T_back") kit_T_back();
if (PART == "web_inner") kit_web_inner();
if (PART == "web_outer") kit_web_outer();
if (PART == "frame_outer") kit_frame_outer();
if (PART == "frame_inner") kit_frame_inner();
if (PART == "hex_axle") kit_hex_axle();
if (PART == "all") {
  translate([0.0, 0.0, 0]) kit_j_front();
  translate([55.0, 0.0, 0]) kit_j_back();
  translate([110.0, 0.0, 0]) kit_k_front();
  translate([165.0, 0.0, 0]) kit_k_back();
  translate([220.0, 0.0, 0]) kit_c_front();
  translate([0.0, -50.0, 0]) kit_c_back();
  translate([55.0, -50.0, 0]) kit_f_front();
  translate([110.0, -50.0, 0]) kit_f_back();
  translate([165.0, -50.0, 0]) kit_U_front();
  translate([220.0, -50.0, 0]) kit_U_back();
  translate([0.0, -100.0, 0]) kit_T_front();
  translate([55.0, -100.0, 0]) kit_T_back();
  translate([110.0, -100.0, 0]) kit_web_inner();
  translate([165.0, -100.0, 0]) kit_web_outer();
  translate([220.0, -100.0, 0]) kit_frame_outer();
  translate([0.0, -150.0, 0]) kit_frame_inner();
  translate([55.0, -150.0, 0]) kit_hex_axle();
}
if (PART == "assembled") {
  translate([6.000,0.000,5.400]) kit_j_front();
  translate([6.000,0.000,7.200]) kit_j_back();
  translate([6.000,0.000,1.800]) kit_k_front();
  translate([6.000,0.000,3.600]) kit_k_back();
  translate([-15.200,-3.120,7.200]) kit_c_front();
  translate([15.200,-3.120,7.200]) kit_c_back();
  translate([-29.918,3.257,9.000]) kit_f_front();
  translate([30.239,-8.698,9.000]) kit_f_back();
  translate([-15.200,-3.120,3.600]) kit_U_front();
  translate([15.200,-3.120,5.400]) kit_U_back();
  translate([-10.781,-18.206,5.400]) kit_T_front();
  translate([26.126,-14.422,1.800]) kit_T_back();
  translate([0.000,0.000,0]) kit_web_inner();
  translate([0.000,0.000,10.800]) kit_web_outer();
  translate([0.000,0.000,12.600]) kit_frame_outer();
  translate([0.000,0.000,-1.800]) kit_frame_inner();
  translate([0.000,0.000,-2.100]) mirror([0,0,1]) kit_hex_axle();
}
