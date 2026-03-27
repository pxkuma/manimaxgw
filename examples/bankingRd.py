from manim import *
import numpy as np

class BankingOfRoad(Scene):
    def construct(self):
        # Part 1: Introduction & Problem
        self.show_problem()
        
        # Part 2: Banking Concept
        self.explain_banking()
        
        # Part 3: Mathematical Derivation
        self.derive_formula()
        
        # Part 4: Critical Speed & Friction
        self.show_critical_speed()
        
        # Part 5: Real-World Examples
        self.show_examples()
        
        # Part 6: Summary
        self.summary()

    def show_problem(self):
        """Part 1: Introduction - Car slipping on flat curve"""
        # Title
        title = Text("Banking of Roads", font_size=60, color=YELLOW)
        subtitle = Text("Physics of Safe Turning", font_size=36, color=WHITE)
        subtitle.next_to(title, DOWN)
        self.play(Write(title), Write(subtitle))
        self.wait(2)
        self.play(FadeOut(title, subtitle))
        
        # Problem statement
        problem_title = Text("The Problem: Flat Curved Road", font_size=48, color=YELLOW)
        self.play(Write(problem_title))
        self.wait(1)
        self.play(problem_title.animate.to_edge(UP))
        
        # Create flat curved road
        road = self.create_road(angle=0, radius=3)
        car = self.create_car()
        car.move_to(road[0].get_start() + RIGHT * 0.5 + UP * 0.5)
        
        self.play(Create(road), Create(car))
        self.wait(1)
        
        # Show values
        values = VGroup(
            Text("v = 20 m/s (72 km/h)", font_size=24),
            Text("r = 50 m", font_size=24),
            Text("μ = 0.3 (Dry asphalt)", font_size=24)
        )
        values.arrange(DOWN, aligned_edge=LEFT)
        values.to_corner(UR)
        
        self.play(Write(values))
        self.wait(1)
        
        # Calculate if car would slip
        v = 20  # m/s
        r = 50  # m
        mu = 0.3
        g = 9.8
        required_friction = v**2 / (r * g)
        
        if required_friction > mu:
            # Car will slip
            slip_text = Text("Car will slip outward!", color=RED, font_size=32)
            slip_text.next_to(problem_title, DOWN)
            self.play(Write(slip_text))
            
            # Show centrifugal force
            centrifugal = Arrow(
                car.get_center(),
                car.get_center() + RIGHT * 1,
                color=ORANGE,
                buff=0,
                stroke_width=6
            )
            centrifugal_label = Text("Centrifugal Force", font_size=20, color=ORANGE)
            centrifugal_label.next_to(centrifugal, RIGHT)
            
            self.play(GrowArrow(centrifugal), Write(centrifugal_label))
            self.wait(1)
            
            # Show friction force
            friction = Arrow(
                car.get_center(),
                car.get_center() + LEFT * 0.8,
                color=RED,
                buff=0,
                stroke_width=6
            )
            friction_label = Text("Friction Force", font_size=20, color=RED)
            friction_label.next_to(friction, LEFT)
            
            self.play(GrowArrow(friction), Write(friction_label))
            self.wait(1)
            
            # Show insufficient friction
            insuf_text = Text("Insufficient friction!", color=RED, font_size=28)
            insuf_text.move_to(DOWN * 2)
            self.play(Write(insuf_text))
            self.wait(2)
            
            self.play(
                FadeOut(centrifugal, centrifugal_label, friction, friction_label, insuf_text, slip_text)
            )
        
        self.play(FadeOut(road, car, values, problem_title))
        self.wait(1)

    def explain_banking(self):
        """Part 2: Banking Concept"""
        title = Text("The Solution: Banked Roads", font_size=48, color=YELLOW)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        # Create banked road
        banked_road = self.create_road(angle=30*DEGREES, radius=3)
        car = self.create_car()
        car.move_to(banked_road[0].get_start() + RIGHT * 0.5 + UP * 0.5)
        
        self.play(Create(banked_road), Create(car))
        self.wait(1)
        
        # Show banking angle
        angle_label = MathTex(r"\theta = 30^\circ", font_size=32, color=YELLOW)
        angle_label.next_to(banked_road, LEFT)
        self.play(Write(angle_label))
        
        # Show cross-section
        cross_section = self.create_cross_section(30*DEGREES)
        cross_section.scale(0.8)
        cross_section.to_edge(RIGHT)
        self.play(Create(cross_section))
        
        # Show forces on cross-section
        self.show_forces_on_banked_road(cross_section, 30*DEGREES)
        
        self.wait(2)
        self.play(FadeOut(title, banked_road, car, angle_label, cross_section))

    def derive_formula(self):
        """Part 3: Mathematical Derivation"""
        title = Text("Mathematical Derivation", font_size=48, color=YELLOW)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        # Create free body diagram
        fbd = self.create_free_body_diagram()
        fbd.scale(0.8)
        fbd.to_edge(LEFT)
        self.play(Create(fbd))
        
        # Step-by-step derivation
        derivation = VGroup()
        
        # Step 1: Vertical equilibrium
        step1_title = Text("Step 1: Vertical Equilibrium", font_size=28, color=BLUE)
        step1_title.next_to(title, DOWN)
        self.play(Write(step1_title))
        
        eq1 = MathTex(r"N\cos\theta = mg", font_size=36)
        eq1.next_to(step1_title, DOWN, buff=0.5)
        self.play(Write(eq1))
        derivation.add(eq1)
        self.wait(2)
        
        # Step 2: Horizontal centripetal force
        step2_title = Text("Step 2: Horizontal Centripetal Force", font_size=28, color=BLUE)
        step2_title.next_to(eq1, DOWN, buff=0.5)
        self.play(Write(step2_title))
        
        eq2 = MathTex(r"N\sin\theta = \frac{mv^2}{r}", font_size=36)
        eq2.next_to(step2_title, DOWN, buff=0.5)
        self.play(Write(eq2))
        derivation.add(eq2)
        self.wait(2)
        
        # Step 3: Divide equations
        step3_title = Text("Step 3: Divide Equations", font_size=28, color=BLUE)
        step3_title.next_to(eq2, DOWN, buff=0.5)
        self.play(Write(step3_title))
        
        eq3 = MathTex(r"\frac{N\sin\theta}{N\cos\theta} = \frac{\frac{mv^2}{r}}{mg}", font_size=36)
        eq3.next_to(step3_title, DOWN, buff=0.5)
        self.play(Write(eq3))
        derivation.add(eq3)
        self.wait(2)
        
        # Step 4: Simplify
        eq4 = MathTex(r"\tan\theta = \frac{v^2}{rg}", font_size=36)
        eq4.next_to(eq3, DOWN, buff=0.5)
        self.play(Transform(eq3.copy(), eq4))
        derivation.add(eq4)
        self.wait(2)
        
        # Step 5: Final formula
        eq5 = MathTex(r"\theta = \tan^{-1}\left(\frac{v^2}{rg}\right)", font_size=40, color=GREEN)
        eq5.next_to(eq4, DOWN, buff=0.5)
        
        box = SurroundingRectangle(eq5, color=YELLOW, buff=0.2)
        self.play(Write(eq5), Create(box))
        self.wait(3)
        
        # Clean up
        self.play(
            FadeOut(title, step1_title, step2_title, step3_title, derivation, box, fbd),
            eq5.animate.move_to(ORIGIN).scale(1.5)
        )
        self.wait(2)
        self.play(FadeOut(eq5))

    def show_critical_speed(self):
        """Part 4: Critical Speed & Friction"""
        title = Text("Critical Speed & Friction Effects", font_size=48, color=YELLOW)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        # Frictionless case
        frictionless_title = Text("Frictionless Case:", font_size=32, color=BLUE)
        frictionless_title.next_to(title, DOWN)
        self.play(Write(frictionless_title))
        
        eq1 = MathTex(r"v_{\text{critical}} = \sqrt{rg\tan\theta}", font_size=36, color=GREEN)
        eq1.next_to(frictionless_title, DOWN, buff=0.5)
        self.play(Write(eq1))
        
        # Example calculation
        example = VGroup(
            Text("Example: θ = 30°, r = 50 m", font_size=24),
            MathTex(r"v_{\text{critical}} = \sqrt{50 \times 9.8 \times \tan(30^\circ)}", font_size=28),
            MathTex(r"v_{\text{critical}} = \sqrt{50 \times 9.8 \times 0.577}", font_size=28),
            MathTex(r"v_{\text{critical}} = 16.8 \text{ m/s} (60.5 \text{ km/h})", font_size=28, color=YELLOW)
        )
        example.arrange(DOWN, aligned_edge=LEFT)
        example.next_to(eq1, DOWN, buff=1)
        self.play(Write(example))
        self.wait(3)
        
        # With friction
        self.play(FadeOut(frictionless_title, eq1, example))
        
        with_friction = Text("With Friction (μ = 0.4):", font_size=32, color=BLUE)
        with_friction.next_to(title, DOWN)
        self.play(Write(with_friction))
        
        # Speed range formulas
        formulas = VGroup(
            MathTex(r"v_{\text{min}} = \sqrt{\frac{rg(\tan\theta - \mu)}{1 + \mu\tan\theta}}", font_size=32),
            MathTex(r"v_{\text{max}} = \sqrt{\frac{rg(\tan\theta + \mu)}{1 - \mu\tan\theta}}", font_size=32)
        )
        formulas.arrange(DOWN, buff=0.5)
        formulas.next_to(with_friction, DOWN, buff=0.5)
        self.play(Write(formulas))
        
        # Speed range visualization
        speed_range = self.create_speed_range_visualization(30, 50, 0.4)
        speed_range.next_to(formulas, DOWN, buff=1)
        self.play(Create(speed_range))
        
        # Safety envelope
        envelope_text = Text("Safety Envelope:", font_size=28, color=GREEN)
        envelope_text.next_to(speed_range, UP)
        self.play(Write(envelope_text))
        
        self.wait(4)
        self.play(FadeOut(title, with_friction, formulas, speed_range, envelope_text))

    def show_examples(self):
        """Part 5: Real-World Examples"""
        title = Text("Real-World Applications", font_size=48, color=YELLOW)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        # Example table
        examples = [
            ("Highway Curve", 25, 200, 90, 17.7),
            ("Race Track", 40, 100, 144, 59.0),
            ("Railway", 30, 300, 108, 16.7),
            ("Airport Runway", 15, 150, 54, 8.7)
        ]
        
        # Create table
        table_data = [
            ["Scenario", "v (m/s)", "r (m)", "v (km/h)", "θ (deg)"],
            ["Highway Curve", "25", "200", "90", "17.7°"],
            ["Race Track", "40", "100", "144", "59.0°"],
            ["Railway", "30", "300", "108", "16.7°"],
            ["Airport Runway", "15", "150", "54", "8.7°"]
        ]
        
        table = Table(
            table_data,
            include_outer_lines=True,
            arrange_in_grid_config={"cell_alignment": RIGHT}
        )
        table.scale(0.4)
        table.next_to(title, DOWN, buff=1)
        
        self.play(Create(table))
        self.wait(3)
        
        # Show visual comparison
        comparison_title = Text("Visual Comparison:", font_size=32, color=BLUE)
        comparison_title.next_to(table, DOWN, buff=1)
        self.play(Write(comparison_title))
        
        # Create small road visualizations
        roads = VGroup()
        for i, (scenario, v, r, v_kmh, theta) in enumerate(examples):
            road = self.create_road(angle=theta*DEGREES, radius=2)
            road.scale(0.3)
            road.move_to(DOWN * 2 + RIGHT * (i - 1.5) * 2)
            
            label = Text(scenario, font_size=12)
            label.next_to(road, UP, buff=0.2)
            
            roads.add(road, label)
        
        self.play(Create(roads))
        self.wait(3)
        
        # Practical limits
        limits_text = Text("Practical Limits: Max banking ~45° for roads", font_size=28, color=YELLOW)
        limits_text.next_to(roads, DOWN, buff=1)
        self.play(Write(limits_text))
        
        self.wait(3)
        self.play(FadeOut(title, table, comparison_title, roads, limits_text))

    def summary(self):
        """Part 6: Summary"""
        title = Text("Summary: Banking of Roads", font_size=60, color=YELLOW)
        self.play(Write(title))
        self.wait(1)
        
        # Key points
        points = VGroup(
            Text("✓ Banking eliminates need for friction at design speed", font_size=24),
            Text("✓ Banking angle depends on square of velocity", font_size=24),
            Text("✓ Radius inversely affects required angle", font_size=24),
            Text("✓ Friction provides safety margin", font_size=24),
            Text("✓ Practical limits exist (max ~45° for roads)", font_size=24),
            Text("✓ Formula: θ = tan⁻¹(v²/(rg))", font_size=28, color=GREEN)
        )
        points.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        points.next_to(title, DOWN, buff=1)
        
        for point in points:
            self.play(Write(point))
            self.wait(0.5)
        
        self.wait(3)
        
        # Final formula display
        final_formula = MathTex(r"\theta = \tan^{-1}\left(\frac{v^2}{rg}\right)", font_size=48, color=YELLOW)
        final_formula.move_to(DOWN * 2)
        
        self.play(
            FadeOut(title, points),
            final_formula.animate.move_to(ORIGIN).scale(1.5)
        )
        
        self.wait(3)
        
        # Thank you
        thank_you = Text("Thank You!", font_size=60, color=BLUE)
        self.play(Transform(final_formula, thank_you))
        self.wait(2)

    # Helper Functions
    def create_road(self, angle=0, radius=3):
        """Create a curved road with banking angle"""
        # Create curved path
        curve = Arc(radius=radius, angle=90*DEGREES)
        
        # Apply banking transformation
        if angle != 0:
            curve.rotate(angle, axis=OUT)
        
        # Add road surface (simplified - just use the curve as road)
        road_surface = curve.copy()
        road_surface.set_stroke(width=10, color=GRAY)
        
        # Road markings
        markings = DashedLine(
            curve.get_start(),
            curve.get_end(),
            dash_length=0.1,
            stroke_width=2,
            color=WHITE
        )
        
        road = VGroup(road_surface, markings)
        return road

    def create_car(self):
        """Create a simple car representation"""
        body = Rectangle(width=1, height=0.5, fill_color=BLUE, fill_opacity=1, stroke_width=2)
        wheels = VGroup(
            Circle(radius=0.1, fill_color=BLACK, fill_opacity=1, stroke_width=1).shift(LEFT * 0.3 + DOWN * 0.25),
            Circle(radius=0.1, fill_color=BLACK, fill_opacity=1, stroke_width=1).shift(RIGHT * 0.3 + DOWN * 0.25)
        )
        car = VGroup(body, wheels)
        return car

    def create_cross_section(self, angle):
        """Create cross-section view of banked road"""
        # Road surface
        surface = Line(LEFT * 2, RIGHT * 2).rotate(angle)
        
        # Angle indicator
        horizontal = Line(LEFT * 2, LEFT * 2 + RIGHT * 1.5)
        arc = Arc(radius=0.5, start_angle=0, angle=angle)
        arc.move_arc_center_to(LEFT * 2)
        
        cross_section = VGroup(surface, horizontal, arc)
        return cross_section

    def show_forces_on_banked_road(self, cross_section, angle):
        """Show force vectors on banked road cross-section"""
        center = cross_section[0].get_center()
        
        # Weight force
        weight = Arrow(
            center,
            center + DOWN * 1.5,
            color=BLUE,
            buff=0,
            stroke_width=6
        )
        weight_label = Text("mg", font_size=20, color=BLUE)
        weight_label.next_to(weight, DOWN)
        
        # Normal force
        normal = Arrow(
            center,
            center + UP * 1.5 * np.cos(angle) + RIGHT * 1.5 * np.sin(angle),
            color=YELLOW,
            buff=0,
            stroke_width=6
        )
        normal_label = Text("N", font_size=20, color=YELLOW)
        normal_label.next_to(normal.get_end(), UP)
        
        # Normal force components
        N_vertical = Arrow(
            center,
            center + UP * 1.5 * np.cos(angle),
            color=YELLOW_D,
            buff=0,
            stroke_width=4,
            stroke_opacity=0.7
        )
        N_horizontal = Arrow(
            center,
            center + RIGHT * 1.5 * np.sin(angle),
            color=YELLOW_D,
            buff=0,
            stroke_width=4,
            stroke_opacity=0.7
        )
        
        # Centripetal force
        centripetal = Arrow(
            center,
            center + LEFT * 1.5,
            color=GREEN,
            buff=0,
            stroke_width=6
        )
        centripetal_label = MathTex(r"\frac{mv^2}{r}", font_size=20, color=GREEN)
        centripetal_label.next_to(centripetal, LEFT)
        
        self.play(GrowArrow(weight), Write(weight_label))
        self.wait(0.5)
        self.play(GrowArrow(normal), Write(normal_label))
        self.wait(0.5)
        self.play(GrowArrow(N_vertical), GrowArrow(N_horizontal))
        self.wait(1)
        self.play(GrowArrow(centripetal), Write(centripetal_label))
        self.wait(2)
        
        self.play(FadeOut(weight, weight_label, normal, normal_label, 
                         N_vertical, N_horizontal, centripetal, centripetal_label))

    def create_free_body_diagram(self):
        """Create free body diagram for banked turn"""
        # Inclined plane
        plane = Line(LEFT * 2, RIGHT * 2).rotate(30*DEGREES)
        
        # Mass/object
        mass = Circle(radius=0.3, fill_color=BLUE, fill_opacity=0.5, stroke_width=2)
        mass.move_to(plane.get_center())
        
        # Forces
        # Weight
        weight = Arrow(
            mass.get_center(),
            mass.get_center() + DOWN * 1.5,
            color=BLUE,
            buff=0,
            stroke_width=6
        )
        weight_label = MathTex(r"mg", font_size=20, color=BLUE)
        weight_label.next_to(weight, DOWN)
        
        # Normal
        normal = Arrow(
            mass.get_center(),
            mass.get_center() + UP * 1.5 * np.cos(30*DEGREES) + RIGHT * 1.5 * np.sin(30*DEGREES),
            color=YELLOW,
            buff=0,
            stroke_width=6
        )
        normal_label = MathTex(r"N", font_size=20, color=YELLOW)
        normal_label.next_to(normal.get_end(), UP)
        
        # Angle indicator
        horizontal = DashedLine(mass.get_center(), mass.get_center() + RIGHT * 1)
        arc = Arc(radius=0.5, start_angle=0, angle=30*DEGREES)
        arc.move_arc_center_to(mass.get_center())
        angle_label = MathTex(r"\theta", font_size=20)
        angle_label.move_to(mass.get_center() + RIGHT * 0.3 + UP * 0.2)
        
        fbd = VGroup(plane, mass, weight, weight_label, normal, normal_label, 
                    horizontal, arc, angle_label)
        
        return fbd

    def create_speed_range_visualization(self, theta_deg, r, mu):
        """Create visualization of speed ranges"""
        theta = theta_deg * DEGREES
        
        # Calculate speed ranges
        g = 9.8
        v_ideal = np.sqrt(r * g * np.tan(theta))
        v_min = np.sqrt(r * g * (np.tan(theta) - mu) / (1 + mu * np.tan(theta)))
        v_max = np.sqrt(r * g * (np.tan(theta) + mu) / (1 - mu * np.tan(theta)))
        
        # Create speed scale
        scale = NumberLine(
            x_range=[0, 40, 5],
            length=8,
            include_numbers=True
        )
        
        # Markers
        ideal_marker = Triangle(fill_color=GREEN, fill_opacity=1, stroke_width=0)
        ideal_marker.scale(0.2)
        ideal_marker.rotate(PI)
        ideal_marker.move_to(scale.n2p(v_ideal) + UP * 0.3)
        
        min_marker = Triangle(fill_color=YELLOW, fill_opacity=1, stroke_width=0)
        min_marker.scale(0.2)
        min_marker.rotate(PI)
        min_marker.move_to(scale.n2p(v_min) + UP * 0.3)
        
        max_marker = Triangle(fill_color=RED, fill_opacity=1, stroke_width=0)
        max_marker.scale(0.2)
        max_marker.rotate(PI)
        max_marker.move_to(scale.n2p(v_max) + UP * 0.3)
        
        # Labels
        ideal_label = Text(f"Ideal: {v_ideal:.1f} m/s", font_size=16, color=GREEN)
        ideal_label.next_to(ideal_marker, UP)
        
        min_label = Text(f"Min: {v_min:.1f} m/s", font_size=16, color=YELLOW)
        min_label.next_to(min_marker, UP)
        
        max_label = Text(f"Max: {v_max:.1f} m/s", font_size=16, color=RED)
        max_label.next_to(max_marker, UP)
        
        # Safe zone
        safe_zone = Rectangle(
            width=(scale.n2p(v_max) - scale.n2p(v_min))[0],
            height=0.5,
            fill_color=GREEN,
            fill_opacity=0.3,
            stroke_width=0
        )
        safe_zone.move_to(scale.n2p((v_min + v_max)/2) + DOWN * 0.5)
        
        visualization = VGroup(scale, safe_zone, ideal_marker, min_marker, max_marker,
                             ideal_label, min_label, max_label)
        
        return visualization

# Run the animation
if __name__ == "__main__":
    scene = BankingOfRoad()
    scene.render()