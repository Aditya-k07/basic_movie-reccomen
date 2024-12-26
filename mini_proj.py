import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  
            password='root',  
            database='mini_proj_te'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        messagebox.showerror("Database Error", f"Error connecting to MySQL: {e}")
        return None

# Main Application Class
class MovieRecommendationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Recommendation System")

        # Login/Register Screen
        self.username_label = tk.Label(root, text="Username")
        self.username_label.pack()
        self.username_entry = tk.Entry(root)
        self.username_entry.pack()

        self.password_label = tk.Label(root, text="Password")
        self.password_label.pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack()

        self.login_button = tk.Button(root, text="Login", command=self.login)
        self.login_button.pack()

        self.register_button = tk.Button(root, text="Register", command=self.register)
        self.register_button.pack()

        # Variables to hold the user ID
        self.user_id = None

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        conn = get_db_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            self.user_id = user[0]
            messagebox.showinfo("Login", "Login Successful")
            self.show_dashboard()
        else:
            messagebox.showerror("Login", "Invalid Credentials")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        conn = get_db_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("Register", "Registration Successful")

    def show_dashboard(self):
        # Clear the login/register UI
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create a frame for scrolling
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        # Add a canvas for scrolling
        canvas = tk.Canvas(frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas to work with the scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create a frame to hold movie entries
        self.movie_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.movie_frame, anchor='nw')

        # Fetch and display movie list
        conn = get_db_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Movies")
        movies = cursor.fetchall()
        cursor.close()
        conn.close()

        self.movie_label = tk.Label(self.movie_frame, text="Movies:")
        self.movie_label.pack()

        for movie in movies:
            movie_info = f"Title: {movie[1]}, Genre: {movie[2]}, Rating: {movie[4]}"
            movie_label = tk.Label(self.movie_frame, text=movie_info)
            movie_label.pack()

            # Rating input and submit button
            rating_entry = tk.Entry(self.movie_frame)
            rating_entry.pack()

            # Submit button for rating
            rate_button = tk.Button(self.movie_frame, text="Rate", 
                                    command=lambda m_id=movie[0], e=rating_entry: self.rate_movie(m_id, e.get()))
            rate_button.pack()

        # Update the scroll region
        self.movie_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # Recommendation button
        recommend_button = tk.Button(self.root, text="Get Recommendations", command=self.get_recommendations)
        recommend_button.pack(pady=10)

        # Exit button
        exit_button = tk.Button(self.root, text="Exit", command=self.root.quit)
        exit_button.pack()

    def rate_movie(self, movie_id, rating):
        try:
            rating = float(rating)
            if rating < 1 or rating > 10:
                raise ValueError("Invalid rating range")

            conn = get_db_connection()
            if conn is None:
                return

            cursor = conn.cursor()
            cursor.execute("INSERT INTO Ratings (user_id, movie_id, rating) VALUES (%s, %s, %s)",
                           (self.user_id, movie_id, rating))
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Rating", "Rating Submitted")

        except ValueError as ve:
            messagebox.showerror("Error", f"Invalid Rating: {ve}")

    def get_recommendations(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return

            cursor = conn.cursor()
            
            # Get genres of movies the user has rated
            cursor.execute("""
                SELECT DISTINCT Movies.genre 
                FROM Movies 
                JOIN Ratings ON Movies.id = Ratings.movie_id 
                WHERE Ratings.user_id = %s
            """, (self.user_id,))
            user_genres = cursor.fetchall()

            if not user_genres:
                messagebox.showinfo("Recommendations", "You haven't rated any movies yet.")
                return

            genre_list = ', '.join(['%s'] * len(user_genres))
            genre_tuple = tuple(genre[0] for genre in user_genres)

            # Fetch movies from the same genres not rated by the user
            cursor.execute(f"""
                SELECT Movies.title, Movies.genre 
                FROM Movies 
                WHERE Movies.genre IN ({genre_list}) 
                AND Movies.id NOT IN (
                    SELECT Ratings.movie_id 
                    FROM Ratings 
                    WHERE Ratings.user_id = %s
                )
            """, genre_tuple + (self.user_id,))
            
            recommendations = cursor.fetchall()
            cursor.close()
            conn.close()

            if recommendations:
                rec_window = tk.Toplevel(self.root)
                rec_window.title("Recommendations")
                rec_label = tk.Label(rec_window, text="Recommended Movies:")
                rec_label.pack()

                for movie in recommendations:
                    movie_info = f"Title: {movie[0]}, Genre: {movie[1]}"
                    movie_label = tk.Label(rec_window, text=movie_info)
                    movie_label.pack()
            else:
                messagebox.showinfo("Recommendations", "No recommendations available.")

        except Error as e:
            messagebox.showerror("Database Error", f"Error fetching recommendations: {e}")

# Initialize and run the Tkinter app
if __name__ == "__main__":
    root = tk.Tk()
    app = MovieRecommendationApp(root)
    root.mainloop()
