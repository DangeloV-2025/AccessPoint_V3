from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, Portfolio, CollegeApplication, Essay
from app import db
from datetime import datetime

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/portfolio')
@login_required
def my_portfolio():
    """View the current user's portfolio"""
    # Get or create portfolio
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id)
        db.session.add(portfolio)
        db.session.commit()

    # Get user's college applications
    applications = CollegeApplication.query.filter_by(user_id=current_user.id).all()

    # Get user's essays
    essays = Essay.query.filter_by(user_id=current_user.id).all()

    return render_template('portfolio/my_portfolio.html',
                          portfolio=portfolio,
                          applications=applications,
                          essays=essays)

@portfolio_bp.route('/portfolio/edit', methods=['GET', 'POST'])
@login_required
def edit_portfolio():
    """Edit the current user's portfolio"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id)
        db.session.add(portfolio)
        db.session.commit()

    if request.method == 'POST':
        portfolio.bio_card = request.form.get('bio_card')
        portfolio.intended_major = request.form.get('intended_major')
        portfolio.is_public = 'is_public' in request.form

        db.session.commit()
        flash('Your portfolio has been updated!', 'success')
        return redirect(url_for('portfolio.my_portfolio'))

    return render_template('portfolio/edit_portfolio.html', portfolio=portfolio)

@portfolio_bp.route('/portfolio/applications', methods=['GET', 'POST'])
@login_required
def manage_applications():
    """Manage college applications"""
    if request.method == 'POST':
        college_name = request.form.get('college_name')
        status = request.form.get('status')
        scholarships = request.form.get('scholarships_awarded')
        honors_program = 'honors_program' in request.form

        if not college_name:
            flash('College name is required.', 'error')
            return redirect(url_for('portfolio.manage_applications'))

        application = CollegeApplication(
            user_id=current_user.id,
            college_name=college_name,
            status=status,
            scholarships_awarded=scholarships,
            honors_program=honors_program
        )

        db.session.add(application)
        db.session.commit()
        flash('College application added!', 'success')
        return redirect(url_for('portfolio.manage_applications'))

    applications = CollegeApplication.query.filter_by(user_id=current_user.id).all()
    return render_template('portfolio/manage_applications.html', applications=applications)

@portfolio_bp.route('/portfolio/applications/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_application(id):
    """Edit a college application"""
    application = CollegeApplication.query.get_or_404(id)

    # Ensure the application belongs to the current user
    if application.user_id != current_user.id:
        flash('You do not have permission to edit this application.', 'error')
        return redirect(url_for('portfolio.manage_applications'))

    if request.method == 'POST':
        application.college_name = request.form.get('college_name')
        application.status = request.form.get('status')
        application.scholarships_awarded = request.form.get('scholarships_awarded')
        application.honors_program = 'honors_program' in request.form

        db.session.commit()
        flash('Application updated!', 'success')
        return redirect(url_for('portfolio.manage_applications'))

    return render_template('portfolio/edit_application.html', application=application)

@portfolio_bp.route('/portfolio/essays', methods=['GET', 'POST'])
@login_required
def manage_essays():
    """Manage essays"""
    applications = CollegeApplication.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        college_application_id = request.form.get('college_application_id')
        is_public = 'is_public' in request.form

        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('portfolio.manage_essays'))

        essay = Essay(
            user_id=current_user.id,
            title=title,
            content=content,
            is_public=is_public
        )

        if college_application_id:
            essay.college_application_id = college_application_id

        db.session.add(essay)
        db.session.commit()
        flash('Essay added!', 'success')
        return redirect(url_for('portfolio.manage_essays'))

    essays = Essay.query.filter_by(user_id=current_user.id).all()
    return render_template('portfolio/manage_essays.html',
                          essays=essays,
                          applications=applications)

@portfolio_bp.route('/portfolios')
def browse_portfolios():
    """Browse public portfolios"""
    portfolios = Portfolio.query.filter_by(is_public=True).all()
    return render_template('portfolio/browse.html', portfolios=portfolios)

@portfolio_bp.route('/portfolio/<uuid:user_id>')
def view_portfolio(user_id):
    """View a specific user's portfolio"""
    portfolio = Portfolio.query.filter_by(user_id=user_id, is_public=True).first_or_404()
    user = User.query.get_or_404(user_id)

    # Get accepted applications
    accepted_applications = CollegeApplication.query.filter_by(
        user_id=user_id,
        status='accepted'
    ).all()

    # Get public essays
    public_essays = Essay.query.filter_by(
        user_id=user_id,
        is_public=True
    ).all()

    return render_template('portfolio/view.html',
                          portfolio=portfolio,
                          user=user,
                          applications=accepted_applications,
                          essays=public_essays)
