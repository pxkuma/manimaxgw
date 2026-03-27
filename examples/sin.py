from manim import *
import numpy as np

config.background_color = BLACK

class TitleScene(Scene):
    def construct(self):
        # Main title
        title = Text("Understanding the Sine Function", 
                    font_size=48, color=BLUE)
        subtitle = Text("A Complete Visual Guide for Beginners", 
                       font_size=36, color=WHITE)
        
        # Position subtitle below title
        subtitle.next_to(title, DOWN, buff=0.5)
        
        # Animate title appearing
        self.play(Write(title, run_time=2))
        self.wait(0.5)
        self.play(FadeIn(subtitle, shift=UP*0.5))
        self.wait(2)
        
        # Fade out
        self.play(FadeOut(title), FadeOut(subtitle))
        self.wait(1)

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
        
        # Show degree and radian markers
        self.play(Write(degree_markers), run_time=2)
        self.wait(0.5)
        self.play(Write(radian_markers), run_time=2)
        self.wait(1)
        
        # Show explanation
        self.play(Write(explanation))
        self.wait(2)
        
        # Clear everything
        self.play(
            FadeOut(axes), FadeOut(circle), FadeOut(radius_line),
            FadeOut(angle_arc), FadeOut(angle_label),
            FadeOut(degree_markers), FadeOut(radian_markers),
            FadeOut(explanation)
        )
        self.wait(1)

class UnitCircleIntroScene(Scene):
    def construct(self):
        # Create unit circle with radius = 1
        axes = Axes(
            x_range=[-1.5, 1.5, 0.5],
            y_range=[-1.5, 1.5, 0.5],
            axis_config={"color": LIGHT_GRAY},
            x_length=6,
            y_length=6
        )
        axes.center()
        
        # Unit circle
        unit_circle = Circle(radius=1, color=GREEN)
        unit_circle.move_to(axes.get_center())
        
        # Radius label
        radius_label = MathTex(r"1", color=GREEN, font_size=32)
        radius_label.move_to(axes.get_center() + RIGHT * 0.5 + UP * 0.5)
        
        # Moving point P on the circle
        point_P = Dot(color=YELLOW, radius=0.08)
        
        # ValueTracker for angle
        theta = ValueTracker(0)
        
        # Function to update point position
        def update_point(mob):
            angle = theta.get_value()
            x = np.cos(angle)
            y = np.sin(angle)
            mob.move_to(axes.c2p(x, y))
        
        point_P.add_updater(update_point)
        
        # Radius line
        radius_line = always_redraw(lambda: Line(
            axes.get_center(),
            point_P.get_center(),
            color=YELLOW
        ))
        
        # Vertical line (sine)
        vertical_line = always_redraw(lambda: Line(
            point_P.get_center(),
            axes.c2p(np.cos(theta.get_value()), 0),
            color=RED,

        ))
        
        # Horizontal line (cosine)
        horizontal_line = always_redraw(lambda: Line(
            point_P.get_center(),
            axes.c2p(0, np.sin(theta.get_value())),
            color=BLUE,

        ))
        
        # Labels
        point_label = MathTex(r"P", color=YELLOW, font_size=32)
        point_label.add_updater(lambda m: m.next_to(point_P, UP, buff=0.1))
        
        sin_label = MathTex(r"\sin(\theta)", color=RED, font_size=32)
        sin_label.add_updater(lambda m: m.next_to(
            vertical_line.get_center(), RIGHT, buff=0.1
        ))
        
        cos_label = MathTex(r"\cos(\theta)", color=BLUE, font_size=32)
        cos_label.add_updater(lambda m: m.next_to(
            horizontal_line.get_center(), UP, buff=0.1
        ))
        
        # Explanation
        explanation = Text("Sine = vertical height of the point on the unit circle", 
                          font_size=28, color=WHITE)
        explanation.to_edge(DOWN, buff=0.5)
        
        # Animation
        self.play(Create(axes), run_time=1)
        self.play(Create(unit_circle), run_time=1)
        self.play(Write(radius_label))
        self.wait(1)
        
        self.add(radius_line, point_P, point_label)
        self.wait(1)
        
        self.play(Create(vertical_line), Write(sin_label))
        self.wait(1)
        
        self.play(Create(horizontal_line), Write(cos_label))
        self.wait(1)
        
        # Animate point moving around the circle
        self.play(theta.animate.set_value(2*PI), run_time=8, rate_func=linear)
        self.wait(1)
        
        # Show explanation
        self.play(Write(explanation))
        self.wait(2)
        
        # Clear
        self.play(
            FadeOut(axes), FadeOut(unit_circle), FadeOut(radius_label),
            FadeOut(radius_line), FadeOut(point_P), FadeOut(point_label),
            FadeOut(vertical_line), FadeOut(horizontal_line),
            FadeOut(sin_label), FadeOut(cos_label),
            FadeOut(explanation)
        )
        self.wait(1)

class SineWaveConstructionScene(Scene):
    def construct(self):
        # Create two sets of axes side by side
        left_axes = Axes(
            x_range=[-1.2, 1.2, 0.5],
            y_range=[-1.2, 1.2, 0.5],
            axis_config={"color": LIGHT_GRAY},
            x_length=4,
            y_length=4
        )
        left_axes.to_edge(LEFT, buff=1)
        
        right_axes = Axes(
            x_range=[0, 2*PI, PI/2],
            y_range=[-1.2, 1.2, 0.5],
            axis_config={"color": LIGHT_GRAY},
            x_length=4,
            y_length=4,
            x_axis_config={"numbers_to_include": [0, PI/2, PI, 3*PI/2, 2*PI]}
        )
        right_axes.to_edge(RIGHT, buff=1)
        
        # Add labels
        left_title = Text("Unit Circle", font_size=32, color=GREEN)
        left_title.next_to(left_axes, UP, buff=0.3)
        
        right_title = Text("Sine Graph", font_size=32, color=BLUE)
        right_title.next_to(right_axes, UP, buff=0.3)
        
        x_label = MathTex(r"\text{Angle } (\theta)", font_size=28, color=WHITE)
        x_label.next_to(right_axes.x_axis, DOWN, buff=0.3)
        
        y_label = MathTex(r"\sin(\theta)", font_size=28, color=RED)
        y_label.next_to(right_axes.y_axis, LEFT, buff=0.3)
        
        # Unit circle on left
        unit_circle = Circle(radius=1, color=GREEN)
        unit_circle.move_to(left_axes.get_center())
        
        # ValueTracker for angle
        theta = ValueTracker(0)
        
        # Point on unit circle
        circle_point = Dot(color=YELLOW, radius=0.06)
        circle_point.add_updater(lambda m: m.move_to(
            left_axes.c2p(np.cos(theta.get_value()), np.sin(theta.get_value()))
        ))
        
        # Radius line
        radius_line = always_redraw(lambda: Line(
            left_axes.get_center(),
            circle_point.get_center(),
            color=YELLOW
        ))
        
        # Vertical line on circle
        vertical_line = always_redraw(lambda: Line(
            circle_point.get_center(),
            left_axes.c2p(np.cos(theta.get_value()), 0),
            color=RED,

        ))
        
        # Point on sine graph
        graph_point = Dot(color=RED, radius=0.06)
        graph_point.add_updater(lambda m: m.move_to(
            right_axes.c2p(theta.get_value(), np.sin(theta.get_value()))
        ))
        
        # Sine wave being traced
        sine_wave = always_redraw(lambda: ParametricFunction(
            lambda t: right_axes.c2p(t, np.sin(t)),
            t_range=[0, theta.get_value()],
            color=BLUE
        ))
        
        # Connection line between circle and graph
        connection_line = always_redraw(lambda: Line(
            circle_point.get_center(),
            graph_point.get_center(),
            color=WHITE,
            stroke_width=1,

        ))
        
        # Animation
        self.play(
            Create(left_axes), Create(right_axes),
            Write(left_title), Write(right_title),
            run_time=2
        )
        self.play(Write(x_label), Write(y_label))
        self.wait(0.5)
        
        self.play(Create(unit_circle))
        self.wait(0.5)
        
        self.add(radius_line, circle_point)
        self.wait(1)
        
        self.play(Create(vertical_line))
        self.wait(0.5)
        
        self.add(sine_wave, graph_point, connection_line)
        self.wait(1)
        
        # Animate the full sine wave construction
        self.play(theta.animate.set_value(2*PI), run_time=10, rate_func=linear)
        self.wait(2)
        
        # Clear
        self.play(
            FadeOut(left_axes), FadeOut(right_axes),
            FadeOut(left_title), FadeOut(right_title),
            FadeOut(x_label), FadeOut(y_label),
            FadeOut(unit_circle), FadeOut(radius_line),
            FadeOut(circle_point), FadeOut(vertical_line),
            FadeOut(sine_wave), FadeOut(graph_point),
            FadeOut(connection_line)
        )
        self.wait(1)

class SinePropertiesScene(Scene):
    def construct(self):
        # Create axes for sine wave
        axes = Axes(
            x_range=[0, 2*PI, PI/2],
            y_range=[-1.5, 1.5, 0.5],
            axis_config={"color": LIGHT_GRAY},
            x_length=7,
            y_length=5,
            x_axis_config={
                "numbers_to_include": [0, PI/2, PI, 3*PI/2, 2*PI],
                "numbers_with_elongated_ticks": [0, PI, 2*PI]
            }
        )
        axes.center()
        
        # Full sine wave
        sine_wave = axes.plot(
            lambda x: np.sin(x),
            x_range=[0, 2*PI],
            color=BLUE
        )
        
        # Labels for x-axis
        pi_labels = VGroup(
            MathTex(r"0", font_size=28).next_to(axes.c2p(0, 0), DOWN, buff=0.2),
            MathTex(r"\pi/2", font_size=28).next_to(axes.c2p(PI/2, 0), DOWN, buff=0.2),
            MathTex(r"\pi", font_size=28).next_to(axes.c2p(PI, 0), DOWN, buff=0.2),
            MathTex(r"3\pi/2", font_size=28).next_to(axes.c2p(3*PI/2, 0), DOWN, buff=0.2),
            MathTex(r"2\pi", font_size=28).next_to(axes.c2p(2*PI, 0), DOWN, buff=0.2)
        )
        
        # Create the scene
        self.play(Create(axes), run_time=1.5)
        self.play(Write(pi_labels))
        self.wait(0.5)
        self.play(Create(sine_wave), run_time=2)
        self.wait(1)
        
        # 1. Amplitude = 1
        peak_dot = Dot(axes.c2p(PI/2, 1), color=RED, radius=0.08)
        trough_dot = Dot(axes.c2p(3*PI/2, -1), color=RED, radius=0.08)
        
        amplitude_brace = BraceBetweenPoints(
            axes.c2p(PI/2, 0),
            axes.c2p(PI/2, 1),
            direction=RIGHT,
            color=RED
        )
        amplitude_label = MathTex(r"\text{Amplitude} = 1", color=RED, font_size=32)
        amplitude_label.next_to(amplitude_brace, RIGHT, buff=0.2)
        
        self.play(
            FadeIn(peak_dot),
            FadeIn(trough_dot)
        )
        self.wait(0.5)
        self.play(
            Create(amplitude_brace),
            Write(amplitude_label)
        )
        self.wait(2)
        
        # 2. Period = 2π
        period_brace = BraceBetweenPoints(
            axes.c2p(0, 1.2),
            axes.c2p(2*PI, 1.2),
            direction=UP,
            color=GREEN
        )
        period_label = MathTex(r"\text{Period} = 2\pi", color=GREEN, font_size=32)
        period_label.next_to(period_brace, UP, buff=0.2)
        
        self.play(
            Create(period_brace),
            Write(period_label)
        )
        self.wait(2)
        
        # 3. Zero crossings
        zero_dots = VGroup(*[
            Dot(axes.c2p(x, 0), color=YELLOW, radius=0.08)
            for x in [0, PI, 2*PI]
        ])
        
        zero_labels = VGroup(*[
            MathTex(r"0", color=YELLOW, font_size=28).next_to(dot, DOWN, buff=0.3)
            for dot in zero_dots
        ])
        
        self.play(
            LaggedStart(*[FadeIn(dot) for dot in zero_dots], lag_ratio=0.3),
            LaggedStart(*[Write(label) for label in zero_labels], lag_ratio=0.3)
        )
        self.wait(2)
        
        # 4. Maximum and minimum
        max_label = MathTex(r"\text{Max at } \pi/2", color=BLUE, font_size=28)
        max_label.next_to(peak_dot, UP, buff=0.2)
        
        min_label = MathTex(r"\text{Min at } 3\pi/2", color=BLUE, font_size=28)
        min_label.next_to(trough_dot, DOWN, buff=0.2)
        
        self.play(
            Write(max_label),
            Write(min_label)
        )
        self.wait(2)
        
        # Clear everything
        self.play(
            FadeOut(axes), FadeOut(sine_wave), FadeOut(pi_labels),
            FadeOut(peak_dot), FadeOut(trough_dot),
            FadeOut(amplitude_brace), FadeOut(amplitude_label),
            FadeOut(period_brace), FadeOut(period_label),
            FadeOut(zero_dots), FadeOut(zero_labels),
            FadeOut(max_label), FadeOut(min_label)
        )
        self.wait(1)

class SineValuesTableScene(Scene):
    def construct(self):
        # Table data
        angles = [
            r"0", r"\pi/6", r"\pi/4", r"\pi/3", 
            r"\pi/2", r"\pi", r"3\pi/2", r"2\pi"
        ]
        
        sine_values = [
            r"0", r"1/2", r"\sqrt{2}/2", r"\sqrt{3}/2",
            r"1", r"0", r"-1", r"0"
        ]
        
        # Create table
        table = VGroup()
        
        # Create headers
        header_angle = Text("θ (angle)", font_size=32, color=YELLOW)
        header_sine = Text("sin(θ)", font_size=32, color=BLUE)
        
        headers = VGroup(header_angle, header_sine)
        headers.arrange(RIGHT, buff=2)
        headers.to_edge(UP, buff=1)
        
        # Create rows
        rows = VGroup()
        for i, (angle, value) in enumerate(zip(angles, sine_values)):
            row = VGroup()
            
            # Angle cell
            angle_tex = MathTex(angle, font_size=28, color=WHITE)
            
            # Sine value cell
            value_tex = MathTex(value, font_size=28, color=WHITE)
            
            row.add(angle_tex, value_tex)
            row.arrange(RIGHT, buff=2)
            rows.add(row)
        
        # Arrange rows vertically
        rows.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        rows.next_to(headers, DOWN, buff=0.8)
        
        # Position headers to align with columns
        header_angle.align_to(rows[0][0], LEFT)
        header_sine.align_to(rows[0][1], LEFT)
        
        # Create unit circle on the right
        circle_axes = Axes(
            x_range=[-1.2, 1.2, 0.5],
            y_range=[-1.2, 1.2, 0.5],
            axis_config={"color": LIGHT_GRAY},
            x_length=3,
            y_length=3
        )
        circle_axes.to_edge(RIGHT, buff=1)
        
        unit_circle = Circle(radius=1, color=GREEN)
        unit_circle.move_to(circle_axes.get_center())
        
        circle_title = Text("Unit Circle", font_size=24, color=GREEN)
        circle_title.next_to(circle_axes, UP, buff=0.3)
        
        # Points on circle for each angle
        angle_values = [0, PI/6, PI/4, PI/3, PI/2, PI, 3*PI/2, 2*PI]
        circle_points = VGroup(*[
            Dot(
                circle_axes.c2p(np.cos(angle), np.sin(angle)),
                color=YELLOW,
                radius=0.05
            )
            for angle in angle_values
        ])
        
        # Animation
        self.play(
            Write(header_angle),
            Write(header_sine)
        )
        self.wait(0.5)
        
        # Animate rows appearing one by one
        for i, row in enumerate(rows):
            # Highlight current row
            highlight_rect = SurroundingRectangle(
                row, color=RED, buff=0.2, stroke_width=2
            )
            
            # Highlight corresponding point on circle
            if i == 0:
                self.play(
                    Create(circle_axes),
                    Create(unit_circle),
                    Write(circle_title)
                )
            
            self.play(
                Write(row),
                Create(highlight_rect),
                FadeIn(circle_points[i], scale=1.5)
            )
            self.wait(0.8)
            
            self.play(FadeOut(highlight_rect))
        
        self.wait(2)
        
        # Clear everything
        self.play(
            FadeOut(headers), FadeOut(rows),
            FadeOut(circle_axes), FadeOut(unit_circle),
            FadeOut(circle_title), FadeOut(circle_points)
        )
        self.wait(1)

class RealLifeExampleScene(Scene):
    def construct(self):
        # Ground line
        ground = Line(
            start=[-5, -2, 0],
            end=[5, -2, 0],
            color=GRAY
        )
        
        # Stick figure person
        # Head
        head = Circle(radius=0.3, color=WHITE)
        head.move_to([-3, -1.2, 0])
        
        # Body
        body = Line(
            start=[-3, -1.5, 0],
            end=[-3, -2, 0],
            color=WHITE
        )
        
        # Arms
        left_arm = Line(
            start=[-3, -1.8, 0],
            end=[-3.5, -1.5, 0],
            color=WHITE
        )
        right_arm = Line(
            start=[-3, -1.8, 0],
            end=[-2.5, -1.5, 0],
            color=WHITE
        )
        
        # Legs
        left_leg = Line(
            start=[-3, -2, 0],
            end=[-3.2, -2.5, 0],
            color=WHITE
        )
        right_leg = Line(
            start=[-3, -2, 0],
            end=[-2.8, -2.5, 0],
            color=WHITE
        )
        
        person = VGroup(head, body, left_arm, right_arm, left_leg, right_leg)
        
        # Pole (wall)
        pole = Line(
            start=[0, -2, 0],
            end=[0, 1, 0],
            color=WHITE,
            stroke_width=8
        )
        
        # Sun
        sun = Circle(radius=0.5, color=YELLOW, fill_opacity=1)
        sun.move_to([4, 2, 0])
        
        # Sun rays
        rays = VGroup()
        for angle in np.linspace(0, 2*PI, 12, endpoint=False):
            ray = Line(
                start=sun.get_center(),
                end=sun.get_center() + 0.8 * np.array([np.cos(angle), np.sin(angle), 0]),
                color=YELLOW,
                stroke_width=2
            )
            rays.add(ray)
        
        sun_group = VGroup(sun, rays)
        
        # Shadow (initially at 45 degrees)
        shadow_length = 1  # when sun is at 45 degrees
        shadow = Line(
            start=[0, -2, 0],
            end=[shadow_length, -2, 0],
            color=GRAY_B,
            stroke_width=6
        )
        
        # Hypotenuse line (from top of pole to end of shadow)
        hypotenuse = Line(
            start=[0, 1, 0],
            end=[shadow_length, -2, 0],
            color=GREEN,
            stroke_width=3
        )
        
        # Angle arc at base
        angle_arc = Arc(
            radius=0.5,
            start_angle=0,
            angle=PI/4,
            color=YELLOW
        )
        angle_arc.move_arc_center_to([0, -2, 0])
        
        # Labels
        theta_label = MathTex(r"\theta", color=YELLOW, font_size=32)
        theta_label.move_to([0.7, -1.7, 0])
        
        opposite_label = Text("opposite", font_size=24, color=RED)
        opposite_label.next_to(pole, RIGHT, buff=0.2)
        
        adjacent_label = Text("adjacent", font_size=24, color=BLUE)
        adjacent_label.next_to(shadow, UP, buff=0.2)
        
        hypotenuse_label = Text("hypotenuse", font_size=24, color=GREEN)
        hypotenuse_label.move_to([0.5, -0.5, 0])
        
        # Formula
        formula = MathTex(r"\sin(\theta) = \frac{\text{opposite}}{\text{hypotenuse}}", 
                         font_size=36, color=WHITE)
        formula.to_edge(UP, buff=0.5)
        
        # Animation sequence
        self.play(Create(ground))
        self.wait(0.5)
        
        # Draw person
        self.play(
            LaggedStart(
                Create(head),
                Create(body),
                Create(left_arm),
                Create(right_arm),
                Create(left_leg),
                Create(right_leg),
                lag_ratio=0.2
            ),
            run_time=2
        )
        self.wait(0.5)
        
        # Draw pole
        self.play(Create(pole))
        self.wait(0.5)
        
        # Draw sun
        self.play(FadeIn(sun_group, scale=0.5))
        self.wait(0.5)
        
        # Draw shadow and triangle
        self.play(Create(shadow))
        self.wait(0.5)
        
        self.play(Create(hypotenuse))
        self.wait(0.5)
        
        # Draw angle and labels
        self.play(Create(angle_arc))
        self.play(Write(theta_label))
        self.wait(0.5)
        
        self.play(Write(opposite_label))
        self.play(Write(adjacent_label))
        self.play(Write(hypotenuse_label))
        self.wait(1)
        
        # Show formula
        self.play(Write(formula))
        self.wait(2)
        
        # Animate sun moving to show changing shadow
        new_sun_pos = [2, 3, 0]
        new_shadow_length = 3  # when sun is higher
        
        # New shadow
        new_shadow = Line(
            start=[0, -2, 0],
            end=[new_shadow_length, -2, 0],
            color=GRAY_B,
            stroke_width=6
        )
        
        # New hypotenuse
        new_hypotenuse = Line(
            start=[0, 1, 0],
            end=[new_shadow_length, -2, 0],
            color=GREEN,
            stroke_width=3
        )
        
        # New angle arc (smaller angle)
        new_angle_arc = Arc(
            radius=0.5,
            start_angle=0,
            angle=np.arctan(1/3),  # opposite/adjacent
            color=YELLOW
        )
        new_angle_arc.move_arc_center_to([0, -2, 0])
        
        # Move sun
        self.play(
            sun_group.animate.move_to(new_sun_pos),
            Transform(shadow, new_shadow),
            Transform(hypotenuse, new_hypotenuse),
            Transform(angle_arc, new_angle_arc),
            run_time=3
        )
        self.wait(2)
        
        # Explanation text
        explanation = Text("This is how sine is used in real life!", 
                          font_size=32, color=WHITE)
        explanation.to_edge(DOWN, buff=0.5)
        
        self.play(Write(explanation))
        self.wait(2)
        
        # Clear everything
        self.play(
            FadeOut(ground), FadeOut(person), FadeOut(pole),
            FadeOut(sun_group), FadeOut(shadow), FadeOut(hypotenuse),
            FadeOut(angle_arc), FadeOut(theta_label),
            FadeOut(opposite_label), FadeOut(adjacent_label),
            FadeOut(hypotenuse_label), FadeOut(formula),
            FadeOut(explanation)
        )
        self.wait(1)

class SineInSOHCAHTOAScene(Scene):
    def construct(self):
        # Draw a right triangle
        triangle_points = [
            [-2, -1, 0],  # A (bottom left)
            [2, -1, 0],   # B (bottom right)
            [2, 2, 0]     # C (top right)
        ]
        
        triangle = Polygon(
            *triangle_points,
            color=WHITE,
            stroke_width=3
        )
        
        # Right angle square
        right_angle = Square(side_length=0.3, color=YELLOW, stroke_width=2)
        right_angle.move_to([1.85, -0.85, 0])
        
        # Angle theta at A
        angle_arc = Arc(
            radius=0.5,
            start_angle=0,
            angle=np.arctan(3/4),  # opposite/adjacent = 3/4
            color=YELLOW
        )
        angle_arc.move_arc_center_to(triangle_points[0])
        
        theta_label = MathTex(r"\theta", color=YELLOW, font_size=32)
        theta_label.move_to([-1.6, -0.7, 0])
        
        # Label sides
        opposite = Line(triangle_points[1], triangle_points[2], color=RED)
        adjacent = Line(triangle_points[0], triangle_points[1], color=BLUE)
        hypotenuse = Line(triangle_points[0], triangle_points[2], color=GREEN)
        
        opposite_label = Text("Opposite", font_size=28, color=RED)
        opposite_label.next_to(opposite, RIGHT, buff=0.1)
        
        adjacent_label = Text("Adjacent", font_size=28, color=BLUE)
        adjacent_label.next_to(adjacent, DOWN, buff=0.1)
        
        hypotenuse_label = Text("Hypotenuse", font_size=28, color=GREEN)
        hypotenuse_label.move_to([0, 0.5, 0])
        
        # SOHCAHTOA text
        sohcahtoa = Text("SOH-CAH-TOA", font_size=42, color=YELLOW)
        sohcahtoa.to_edge(UP, buff=0.5)
        
        soh_text = Text("SOH = Sine, Opposite, Hypotenuse", font_size=32, color=WHITE)
        soh_text.next_to(sohcahtoa, DOWN, buff=0.5)
        
        # Sine formula
        sine_formula = MathTex(r"\sin(\theta) = \frac{\text{Opposite}}{\text{Hypotenuse}}", 
                              font_size=36, color=WHITE)
        sine_formula.next_to(soh_text, DOWN, buff=0.8)
        
        # Highlighted version
        highlighted_formula = MathTex(r"\sin(\theta) = \frac{\text{Opposite}}{\text{Hypotenuse}}", 
                                     font_size=36, color=RED)
        highlighted_formula.move_to(sine_formula.get_center())
        
        # Numerical example
        example_text = Text("Example:", font_size=32, color=WHITE)
        example_text.next_to(sine_formula, DOWN, buff=0.8)
        
        example_values = MathTex(r"\text{If } \text{Opposite} = 3, \text{Hypotenuse} = 5", 
                                font_size=32, color=WHITE)
        example_values.next_to(example_text, DOWN, buff=0.3)
        
        example_calc = MathTex(r"\sin(\theta) = \frac{3}{5} = 0.6", 
                              font_size=32, color=GREEN)
        example_calc.next_to(example_values, DOWN, buff=0.3)
        
        # Animation sequence
        self.play(Create(triangle), run_time=1.5)
        self.wait(0.5)
        
        self.play(Create(right_angle))
        self.wait(0.5)
        
        self.play(Create(angle_arc), Write(theta_label))
        self.wait(0.5)
        
        # Show side labels
        self.play(
            Write(opposite_label),
            Write(adjacent_label),
            Write(hypotenuse_label)
        )
        self.wait(1)
        
        # Show SOHCAHTOA
        self.play(Write(sohcahtoa))
        self.wait(0.5)
        self.play(Write(soh_text))
        self.wait(1)
        
        # Show sine formula
        self.play(Write(sine_formula))
        self.wait(1)
        
        # Highlight the formula
        self.play(Transform(sine_formula, highlighted_formula))
        self.wait(2)
        
        # Show example
        self.play(Write(example_text))
        self.wait(0.5)
        self.play(Write(example_values))
        self.wait(0.5)
        self.play(Write(example_calc))
        self.wait(2)
        
        # Clear everything
        self.play(
            FadeOut(triangle), FadeOut(right_angle),
            FadeOut(angle_arc), FadeOut(theta_label),
            FadeOut(opposite_label), FadeOut(adjacent_label),
            FadeOut(hypotenuse_label), FadeOut(sohcahtoa),
            FadeOut(soh_text), FadeOut(sine_formula),
            FadeOut(example_text), FadeOut(example_values),
            FadeOut(example_calc)
        )
        self.wait(1)

class SoundWaveRealLifeScene(Scene):
    def construct(self):
        # Create axes for sound wave
        axes = Axes(
            x_range=[0, 4*PI, PI],
            y_range=[-1.5, 1.5, 0.5],
            axis_config={"color": LIGHT_GRAY},
            x_length=6,
            y_length=3
        )
        axes.center().shift(UP)
        
        # ValueTracker for phase shift
        phase = ValueTracker(0)
        
        # Sine wave that moves (sound wave)
        sound_wave = always_redraw(lambda: axes.plot(
            lambda x: np.sin(x + phase.get_value()),
            x_range=[0, 4*PI],
            color=BLUE,
            stroke_width=4
        ))
        
        # Wave label
        wave_label = Text("Sound Wave", font_size=32, color=BLUE)
        wave_label.next_to(axes, UP, buff=0.3)
        
        # Speaker on left
        speaker_base = Rectangle(
            width=0.8, height=1.2, color=WHITE, fill_opacity=0.3
        )
        speaker_base.move_to([-4, 0.5, 0])
        
        speaker_cone = Circle(radius=0.4, color=WHITE, fill_opacity=0.3)
        speaker_cone.next_to(speaker_base, RIGHT, buff=0)
        
        speaker = VGroup(speaker_base, speaker_cone)
        
        # Sound waves coming from speaker
        sound_lines = always_redraw(lambda: VGroup(*[
            Arc(
                radius=0.5 + i*0.3 + phase.get_value() % 0.3,
                start_angle=-PI/4,
                angle=PI/2,
                color=BLUE,
                stroke_width=2
            ).move_arc_center_to(speaker_cone.get_center())
            for i in range(3)
        ]))
        
        # Listener on right
        # Head
        listener_head = Circle(radius=0.4, color=WHITE)
        listener_head.move_to([4, 0.5, 0])
        
        # Body
        listener_body = Line(
            start=[4, 0.1, 0],
            end=[4, -0.5, 0],
            color=WHITE
        )
        
        # Ear (emphasized)
        ear = Circle(radius=0.1, color=RED, fill_opacity=0.5)
        ear.move_to([3.7, 0.5, 0])
        
        listener = VGroup(listener_head, listener_body, ear)
        
        # Ear label
        ear_label = Text("Listening", font_size=24, color=RED)
        ear_label.next_to(ear, LEFT, buff=0.2)
        
        # Explanation text
        explanation = Text("Sound travels as a sine wave — Sine is everywhere in nature!", 
                          font_size=28, color=WHITE)
        explanation.to_edge(DOWN, buff=0.5)
        
        # Animation
        self.play(Create(axes), run_time=1)
        self.play(Write(wave_label))
        self.wait(0.5)
        
        self.add(sound_wave)
        self.wait(0.5)
        
        # Create speaker
        self.play(Create(speaker))
        self.wait(0.5)
        
        # Create listener
        self.play(Create(listener))
        self.play(Write(ear_label))
        self.wait(0.5)
        
        # Add sound lines from speaker
        self.add(sound_lines)
        
        # Animate the wave moving
        self.play(
            phase.animate.set_value(4*PI),
            run_time=6,
            rate_func=linear
        )
        self.wait(1)
        
        # Show explanation
        self.play(Write(explanation))
        self.wait(2)
        
        # Clear everything
        self.play(
            FadeOut(axes), FadeOut(sound_wave), FadeOut(wave_label),
            FadeOut(speaker), FadeOut(sound_lines),
            FadeOut(listener), FadeOut(ear_label),
            FadeOut(explanation)
        )
        self.wait(1)

class SummaryScene(Scene):
    def construct(self):
        # Title
        title = Text("Summary: Key Points About Sine", 
                    font_size=48, color=BLUE)
        title.to_edge(UP, buff=0.5)
        
        # Bullet points
        bullets = VGroup(
            Text("• Sine is the vertical component of a unit circle", 
                font_size=32, color=WHITE),
            Text("• sin(θ) = Opposite / Hypotenuse in a right triangle", 
                font_size=32, color=WHITE),
            Text("• Amplitude = 1, Period = 2π", 
                font_size=32, color=WHITE),
            Text("• Key values: 0, 0.5, √2/2, √3/2, 1", 
                font_size=32, color=WHITE),
            Text("• Sine waves model sound, light, and many natural phenomena", 
                font_size=32, color=WHITE)
        )
        
        # Arrange bullets
        bullets.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        bullets.next_to(title, DOWN, buff=0.8)
        bullets.to_edge(LEFT, buff=1.5)
        
        # Visual examples next to bullets
        # 1. Unit circle example
        circle_axes = Axes(
            x_range=[-0.8, 0.8, 0.5],
            y_range=[-0.8, 0.8, 0.5],
            axis_config={"color": LIGHT_GRAY},
            x_length=1.5,
            y_length=1.5
        )
        circle_axes.move_to([3, 2.5, 0])
        
        unit_circle = Circle(radius=0.7, color=GREEN)
        unit_circle.move_to(circle_axes.get_center())
        
        point = Dot(circle_axes.c2p(np.cos(PI/4), np.sin(PI/4)), color=YELLOW)
        vertical_line = Line(
            point.get_center(),
            circle_axes.c2p(np.cos(PI/4), 0),
            color=RED
        )
        
        circle_example = VGroup(circle_axes, unit_circle, point, vertical_line)
        
        # 2. Right triangle example
        triangle = Polygon(
            [-0.5, -0.5, 0],
            [0.5, -0.5, 0],
            [0.5, 0.5, 0],
            color=WHITE
        )
        triangle.move_to([3, 0.5, 0])
        
        # 3. Sine wave example
        wave_axes = Axes(
            x_range=[0, 2*PI, PI],
            y_range=[-1, 1, 0.5],
            axis_config={"color": LIGHT_GRAY},
            x_length=2.5,
            y_length=1.2
        )
        wave_axes.move_to([3, -1.5, 0])
        
        sine_wave = wave_axes.plot(
            lambda x: np.sin(x),
            x_range=[0, 2*PI],
            color=BLUE
        )
        
        wave_example = VGroup(wave_axes, sine_wave)
        
        # Final message
        final_message = Text("You now understand the Sine Function!", 
                           font_size=42, color=GREEN)
        final_message.to_edge(DOWN, buff=1)
        
        # Animation sequence
        self.play(Write(title))
        self.wait(1)
        
        # Animate bullets appearing one by one
        for i, bullet in enumerate(bullets):
            self.play(Write(bullet), run_time=1)
            
            # Show corresponding visual example
            if i == 0:
                self.play(FadeIn(circle_example, scale=0.8))
            elif i == 1:
                self.play(FadeIn(triangle, scale=0.8))
            elif i == 2:
                # Highlight amplitude and period on wave
                amp_brace = BraceBetweenPoints(
                    wave_axes.c2p(PI/2, 0),
                    wave_axes.c2p(PI/2, 1),
                    direction=RIGHT,
                    color=RED
                )
                amp_label = MathTex(r"1", color=RED, font_size=20)
                amp_label.next_to(amp_brace, RIGHT, buff=0.1)
                
                period_brace = BraceBetweenPoints(
                    wave_axes.c2p(0, 1.2),
                    wave_axes.c2p(2*PI, 1.2),
                    direction=UP,
                    color=GREEN
                )
                period_label = MathTex(r"2\pi", color=GREEN, font_size=20)
                period_label.next_to(period_brace, UP, buff=0.1)
                
                self.play(FadeIn(wave_example, scale=0.8))
                self.play(
                    Create(amp_brace),
                    Write(amp_label),
                    Create(period_brace),
                    Write(period_label)
                )
                self.wait(0.5)
            elif i == 3:
                # Show key values
                values_text = MathTex(
                    r"0,\ \frac{1}{2},\ \frac{\sqrt{2}}{2},\ \frac{\sqrt{3}}{2},\ 1",
                    font_size=28,
                    color=YELLOW
                )
                values_text.next_to(wave_example, DOWN, buff=0.3)
                self.play(Write(values_text))
                self.wait(0.5)
            
            self.wait(0.5)
        
        self.wait(1)
        
        # Show final message
        self.play(Write(final_message))
        self.wait(3)
        
        # Final fade out
        self.play(
            FadeOut(title),
            FadeOut(bullets),
            FadeOut(circle_example),
            FadeOut(triangle),
            FadeOut(wave_example),
            FadeOut(final_message)
        )
        self.wait(1)

if __name__ == "__main__":
    scenes = [
        TitleScene,
        WhatIsAnAngleScene,
        UnitCircleIntroScene,
        SineWaveConstructionScene,
        SinePropertiesScene,
        SineValuesTableScene,
        RealLifeExampleScene,
        SineInSOHCAHTOAScene,
        SoundWaveRealLifeScene,
        SummaryScene
    ]
    
    # To render a specific scene, use:
    # manim -pql script.py SceneName
    # For example: manim -pql script.py TitleScene
    pass