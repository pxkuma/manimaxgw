from manim import *
import numpy as np

class WhatIsAnAngleScene(Scene):
    def construct(self):
        # Create axes
        axes = Axes(
            x_range=[-1.5, 1.5, 1],
            y_range=[-1.5, 1.5, 1],
            axis_config={"color": LIGHT_GRAY},
            x_length=5,
            y_length=5
        )
        axes.center()
        
        # Create circle
        circle = Circle(radius=1.5, color=GREEN)
        circle.move_to(axes.get_center())
        
        # Initial radius line
        radius_line = Line(
            axes.get_center(),
            axes.get_center() + RIGHT * 1.5,
            color=YELLOW
        )
        
        # Angle arc
        angle_arc = Arc(
            radius=0.5,
            start_angle=0,
            angle=0,
            color=YELLOW
        )
        
        # Angle label
        angle_label = MathTex(r"\theta", color=YELLOW, font_size=36)
        
        # Create degree markers
        degree_markers = VGroup()
        radian_markers = VGroup()
        
        angles = [0, PI/2, PI, 3*PI/2, 2*PI]
        degree_texts = ["0°", "90°", "180°", "270°", "360°"]
        radian_texts = ["0", r"\pi/2", r"\pi", r"3\pi/2", r"2\pi"]
        
        for i, (angle, deg_text, rad_text) in enumerate(zip(angles, degree_texts, radian_texts)):
            point = axes.get_center() + 1.7 * np.array([np.cos(angle), np.sin(angle), 0])
            
            # Degree marker
            deg_marker = MathTex(deg_text, color=WHITE, font_size=24)
            deg_marker.move_to(point * 1.2)
            
            # Radian marker
            rad_marker = MathTex(rad_text, color=BLUE, font_size=24)
            rad_marker.next_to(deg_marker, DOWN, buff=0.2)
            
            degree_markers.add(deg_marker)
            radian_markers.add(rad_marker)
        
        # Explanation text
        explanation = Text("Angle = rotation from positive x-axis", 
                          font_size=32, color=WHITE)
        explanation.to_edge(DOWN, buff=0.5)
        
        # Animation sequence
        self.play(Create(axes), run_time=1)
        self.play(Create(circle), run_time=1)
        self.wait(0.5)
        
        self.play(Create(radius_line), Create(angle_arc))
        self.play(Write(angle_label.next_to(angle_arc, RIGHT, buff=0.1)))
        self.wait(1)
        
        # Animate rotation
        for angle in [PI/2, PI, 3*PI/2, 2*PI]:
            new_line = Line(
                axes.get_center(),
                axes.get_center() + 1.5 * np.array([np.cos(angle), np.sin(angle), 0]),
                color=YELLOW
            )
            new_arc = Arc(
                radius=0.5,
                start_angle=0,
                angle=angle,
                color=YELLOW
            )
            self.play(
                Transform(radius_line, new_line),
                Transform(angle_arc, new_arc),
                run_time=1.5
            )
            self.wait(0.5)
