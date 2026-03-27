from manim import *
import numpy as np

class BankingOfRoad(Scene):
    def construct(self):
        # Title
        title = Text("Banking of Roads", font_size=48, color=BLUE)
        subtitle = Text("The Physics Behind Curved Road Design", font_size=24, color=GRAY)
        subtitle.next_to(title, DOWN)
        
        self.play(Write(title), Write(subtitle))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))
        
        # Introduction
        self.show_introduction()
        self.show_problem_statement()
        self.show_banking_concept()
        self.derive_banking_angle()
        self.show_critical_speed()
        self.show_real_world_applications()
        self.show_summary()

    def show_introduction(self):
        title = Text("Why Do Roads Need Banking?", font_size=36, color=YELLOW)
        self.play(Write(title))
        self.wait(1)
        
        # Show car on flat curve
        road = self.create_flat_road()
        car = self.create_car()
        
        self.play(Create(road))
        self.play(Create(car))
        
        # Animate car slipping
        self.play(car.animate.shift(RIGHT * 0.5), run_time=2)
        slip_arrow = Arrow(UP, DOWN, color=RED).next_to(car, UP)
        slip_text = Text("Slipping!", color=RED, font_size=18).next_to(slip_arrow, UP)
        
        self.play(GrowArrow(slip_arrow), Write(slip_text))
        self.wait(2)
        
        self.play(FadeOut(road), FadeOut(car), FadeOut(slip_arrow), FadeOut(slip_text), FadeOut(title))

    def show_problem_statement(self):
        title = Text("The Problem: Centrifugal Force", font_size=36, color=ORANGE)
        self.play(Write(title))
        self.wait(1)
        
        # Create force diagram
        circle = Circle(radius=2, color=WHITE)
        dot = Dot(color=RED).move_to(circle.point_at_angle(0))
        
        # Forces
        centripetal_force = Arrow(
            dot.get_center(), 
            dot.get_center() + LEFT * 1.5, 
            color=BLUE, 
            buff=0
        )
        centrifugal_force = Arrow(
            dot.get_center(), 
            dot.get_center() + RIGHT * 1.5, 
            color=RED, 
            buff=0
        )
        
        force_labels = VGroup(
            Text("F_c (Centripetal)", color=BLUE, font_size=16).next_to(centripetal_force, LEFT),
            Text("F_{cf} (Centrifugal)", color=RED, font_size=16).next_to(centrifugal_force, RIGHT)
        )
        
        self.play(Create(circle), Create(dot))
        self.play(GrowArrow(centripetal_force), GrowArrow(centrifugal_force))
        self.play(Write(force_labels))
        
        explanation = Text(
            "On curved paths, vehicles experience\noutward centrifugal force",
            font_size=20,
            color=WHITE
        ).to_edge(DOWN)
        
        self.play(Write(explanation))
        self.wait(3)
        
        self.play(FadeOut(VGroup(circle, dot, centripetal_force, centrifugal_force, force_labels, explanation, title)))

    def show_banking_concept(self):
        title = Text("The Solution: Banked Roads", font_size=36, color=GREEN)
        self.play(Write(title))
        
        # Show banked road
        banked_road = self.create_banked_road(angle=30*DEGREES)
        car = self.create_car()
        
        self.play(Create(banked_road))
        self.play(Create(car))
        
        # Show normal force components
        normal_force = Arrow(
            car.get_center(), 
            car.get_center() + UP * 1.5, 
            color=YELLOW
        )
        normal_label = Text("N", color=YELLOW, font_size=16).next_to(normal_force, RIGHT)
        
        # Break down normal force
        theta = 30 * DEGREES
        N_horizontal = normal_force.copy().scale(np.sin(theta), about_point=car.get_center())
        N_vertical = normal_force.copy().scale(np.cos(theta), about_point=car.get_center())
        
        N_horizontal.set_color(PURPLE)
        N_vertical.set_color(ORANGE)
        
        self.play(GrowArrow(normal_force), Write(normal_label))
        self.wait(1)
        
        explanation = Text(
            "Banking allows normal force to provide\nnecessary centripetal force",
            font_size=20,
            color=WHITE
        ).to_edge(DOWN)
        
        self.play(Write(explanation))
        self.wait(3)
        
        self.play(FadeOut(VGroup(banked_road, car, normal_force, normal_label, explanation, title)))

    def derive_banking_angle(self):
        title = Text("Deriving the Banking Angle Formula", font_size=36, color=TEAL)
        self.play(Write(title))
        
        # Show the free body diagram
        fbd = self.create_free_body_diagram()
        self.play(Create(fbd))
        
        # Step-by-step derivation
        steps = VGroup(
            Text("Step 1: Force Balance", font_size=24, color=YELLOW),
            MathTex("N\\cos\\theta = mg", color=WHITE),
            Text("Step 2: Horizontal Force", font_size=24, color=YELLOW),
            MathTex("N\\sin\\theta = \\frac{mv^2}{r}", color=WHITE),
            Text("Step 3: Divide Equations", font_size=24, color=YELLOW),
            MathTex("\\tan\\theta = \\frac{v^2}{rg}", color=GREEN)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.8)
        
        steps.to_edge(RIGHT)
        
        for step in steps:
            self.play(Write(step))
            self.wait(1)
        
        final_formula = MathTex("\\theta = \\tan^{-1}\\left(\\frac{v^2}{rg}\\right)", color=GREEN)
        final_formula.scale(1.2).to_edge(DOWN)
        
        self.play(Write(final_formula))
        self.wait(3)
        
        self.play(FadeOut(VGroup(fbd, steps, final_formula, title)))

    def show_critical_speed(self):
        title = Text("Critical Speed and Friction", font_size=36, color=RED)
        self.play(Write(title))
        
        # Show the modified formula with friction
        formula_with_friction = VGroup(
            MathTex("\\tan\\theta = \\frac{v^2}{rg} - \\mu_s", color=ORANGE),
            Text("With Friction Considered", font_size=20, color=GRAY)
        ).arrange(DOWN)
        
        self.play(Write(formula_with_friction))
        self.wait(2)
        
        # Show speed ranges
        speed_ranges = VGroup(
            Text("Speed Ranges:", font_size=24, color=YELLOW),
            Text("v < v_critical: Vehicle tends to slip inward", color=BLUE),
            Text("v = v_critical: Ideal banking condition", color=GREEN),
            Text("v > v_critical: Vehicle tends to slip outward", color=RED)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.8)
        
        speed_ranges.to_edge(DOWN)
        
        self.play(Write(speed_ranges))
        self.wait(3)
        
        self.play(FadeOut(VGroup(formula_with_friction, speed_ranges, title)))

    def show_real_world_applications(self):
        title = Text("Real-World Applications", font_size=36, color=PURPLE)
        self.play(Write(title))
        
        applications = VGroup(
            Text("• Race Tracks: High banking angles for high speeds", color=GREEN),
            Text("• Highway Curves: Moderate banking for safety", color=BLUE),
            Text("• Railway Tracks: Special banking for trains", color=ORANGE),
            Text("• Airport Runways: Banking for turning aircraft", color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.8)
        
        self.play(Write(applications))
        self.wait(3)
        
        # Show example calculation
        example_title = Text("Example Calculation:", font_size=24, color=WHITE)
        example = VGroup(
            MathTex("v = 60\\,km/h = 16.67\\,m/s", color=BLUE),
            MathTex("r = 100\\,m", color=BLUE),
            MathTex("g = 9.8\\,m/s^2", color=BLUE),
            MathTex("\\theta = \\tan^{-1}\\left(\\frac{(16.67)^2}{100 \\times 9.8}\\right)", color=GREEN),
            MathTex("\\theta \\approx 15.4^\\circ", color=GREEN)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.8)
        
        example.next_to(applications, DOWN, buff=0.5)
        example_title.next_to(example, UP)
        
        self.play(Write(example_title), Write(example))
        self.wait(3)
        
        self.play(FadeOut(VGroup(title, applications, example_title, example)))

    def show_summary(self):
        title = Text("Summary: Banking of Roads", font_size=36, color=GOLD)
        self.play(Write(title))
        
        summary_points = VGroup(
            Text("✓ Prevents slipping on curved paths", color=GREEN),
            Text("✓ Uses normal force for centripetal acceleration", color=BLUE),
            Text("✓ Banking angle depends on speed and radius", color=ORANGE),
            Text("✓ Critical speed ensures optimal safety", color=YELLOW),
            Text("✓ Widely used in transportation engineering", color=PURPLE)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.8)
        
        summary_points.next_to(title, DOWN, buff=0.5)
        
        self.play(Write(summary_points))
        self.wait(3)
        
        final_formula = MathTex("\\theta = \\tan^{-1}\\left(\\frac{v^2}{rg}\\right)", color=GREEN)
        final_formula.scale(1.2).to_edge(DOWN)
        
        self.play(Write(final_formula))
        self.wait(2)
        
        self.play(FadeOut(VGroup(title, summary_points, final_formula)))

    def create_flat_road(self):
        # Create a flat curved road
        road = ParametricFunction(
            lambda t: np.array([t, 0.2 * np.sin(t/2), 0]),
            t_range=[-3, 3],
            color=GRAY
        )
        return road

    def create_banked_road(self, angle=30*DEGREES):
        # Create a banked road surface
        road = ParametricFunction(
            lambda t: np.array([
                t,
                0.2 * np.sin(t/2) + 0.5 * np.sin(angle) * (t/3),
                0
            ]),
            t_range=[-3, 3],
            color=GRAY
        )
        return road

    def create_car(self):
        # Create a simple car representation
        car_body = Rectangle(width=0.8, height=0.4, color=RED, fill_opacity=1)
        car_wheels = VGroup(
            Circle(radius=0.1, color=BLACK, fill_opacity=1).shift(LEFT * 0.2 + DOWN * 0.3),
            Circle(radius=0.1, color=BLACK, fill_opacity=1).shift(RIGHT * 0.2 + DOWN * 0.3)
        )
        car = VGroup(car_body, car_wheels)
        return car

    def create_free_body_diagram(self):
        # Create a free body diagram for banked road
        diagram = VGroup()
        
        # Inclined plane
        plane = Line(LEFT * 2, RIGHT * 2).rotate(30 * DEGREES)
        diagram.add(plane)
        
        # Object on plane
        obj = Dot(color=RED)
        diagram.add(obj)
        
        # Forces
        mg = Arrow(obj.get_center(), obj.get_center() + DOWN * 1.5, color=BLUE)
        N = Arrow(obj.get_center(), obj.get_center() + UP * 1.5, color=YELLOW)
        fc = Arrow(obj.get_center(), obj.get_center() + LEFT * 1.5, color=RED)
        
        diagram.add(mg, N, fc)
        
        # Labels
        labels = VGroup(
            MathTex("mg", color=BLUE).next_to(mg, DOWN),
            MathTex("N", color=YELLOW).next_to(N, UP),
            MathTex("F_c", color=RED).next_to(fc, LEFT)
        )
        diagram.add(labels)
        
        # Angle indicator
        angle_arc = Arc(radius=0.5, angle=30*DEGREES, color=WHITE)
        angle_text = MathTex("\\theta", color=WHITE).next_to(angle_arc, RIGHT)
        diagram.add(angle_arc, angle_text)
        
        return diagram

# Additional scene for interactive demonstration
class BankingInteractive(Scene):
    def construct(self):
        title = Text("Interactive Banking Demonstration", font_size=36, color=BLUE)
        self.play(Write(title))
        
        # Create adjustable parameters
        speed_value = ValueTracker(15)  # m/s
        radius_value = ValueTracker(50)  # meters
        
        # Create road and car
        road = always_redraw(lambda: self.create_banked_road(
            np.arctan(speed_value.get_value()**2 / (radius_value.get_value() * 9.8))
        ))
        car = self.create_car()
        
        # Display current values
        speed_text = always_redraw(lambda: Text(
            f"Speed: {speed_value.get_value():.1f} m/s", 
            font_size=20
        ).to_edge(UP))
        
        radius_text = always_redraw(lambda: Text(
            f"Radius: {radius_value.get_value():.0f} m", 
            font_size=20
        ).next_to(speed_text, DOWN))
        
        angle_text = always_redraw(lambda: Text(
            f"Banking Angle: {np.degrees(np.arctan(speed_value.get_value()**2 / (radius_value.get_value() * 9.8))):.1f}°", 
            font_size=20,
            color=YELLOW
        ).next_to(radius_text, DOWN))
        
        self.play(Create(road), Create(car))
        self.play(Write(speed_text), Write(radius_text), Write(angle_text))
        
        # Animate parameter changes
        self.play(speed_value.animate.set_value(25), run_time=3)
        self.wait(1)
        self.play(radius_value.animate.set_value(100), run_time=3)
        self.wait(1)
        self.play(speed_value.animate.set_value(10), radius_value.animate.set_value(30), run_time=3)
        self.wait(2)
        
        self.play(FadeOut(VGroup(road, car, speed_text, radius_text, angle_text, title)))
    
    def create_banked_road(self, angle):
        return ParametricFunction(
            lambda t: np.array([
                t,
                0.2 * np.sin(t/2) + 0.5 * np.sin(angle) * (t/3),
                0
            ]),
            t_range=[-3, 3],
            color=GRAY
        )
    
    def create_car(self):
        car_body = Rectangle(width=0.8, height=0.4, color=RED, fill_opacity=1)
        car_wheels = VGroup(
            Circle(radius=0.1, color=BLACK, fill_opacity=1).shift(LEFT * 0.2 + DOWN * 0.3),
            Circle(radius=0.1, color=BLACK, fill_opacity=1).shift(RIGHT * 0.2 + DOWN * 0.3)
        )
        return VGroup(car_body, car_wheels)

# Run the animation
if __name__ == "__main__":
    scene = BankingOfRoad()
    scene.render()