import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import { Alert, EmptyState, Modal, VerticalNav } from 'patternfly-react';
import _ from 'lodash';
import { routes } from '../routes';
import { authorizeUser, getUser, logoutUser } from '../redux/actions/userActions';
import { getStatus } from '../redux/actions/statusActions';
import helpers from '../common/helpers';
import About from './about/about';
import AddSourceWizard from './addSourceWizard/addSourceWizard';
import CreateCredentialDialog from './createCredentialDialog/createCredentialDialog';
import Content from './content/content';
import ToastNotificationsList from './toastNotificationsList/toastNotificationsList';
import ConfirmationModal from './confirmationModal/confirmationModal';
import MastheadOptions from './mastheadOptions/mastheadOptions';
import productTitle from '../styles/images/title.svg';
import rhProductTitle from '../styles/images/brand/title.svg';

class App extends React.Component {
  constructor() {
    super();

    this.menu = routes();
    this.state = {
      aboutShown: false
    };

    helpers.bindMethods(this, ['showAbout', 'closeAbout']);
  }

  componentDidMount() {
    this.props.authorizeUser();
    this.props.getStatus();
  }

  componentWillReceiveProps(nextProps) {
    if (_.get(nextProps, 'session.loggedIn') && !_.get(this.props, 'session.loggedIn')) {
      this.props.getUser();
    }
  }

  navigateTo(path) {
    const { history } = this.props;
    history.push(path);
  }

  showAbout() {
    this.setState({ aboutShown: true });
  }

  closeAbout() {
    this.setState({ aboutShown: false });
  }

  renderMenuItems() {
    const { location } = this.props;

    const activeItem = this.menu.find(item => _.startsWith(location.pathname, item.to));

    return this.menu.map(item => (
      <VerticalNav.Item
        key={item.to}
        title={item.title}
        iconClass={item.iconClass}
        active={item === activeItem || (!activeItem && item.redirect)}
        onClick={() => this.navigateTo(item.to)}
      />
    ));
  }

  renderMenuActions() {
    const { logoutUser } = this.props;

    return [
      <VerticalNav.Item key="about" className="collapsed-nav-item" title="About" onClick={() => this.showAbout()} />,
      <VerticalNav.Item key="logout" className="collapsed-nav-item" title="Logout" onClick={logoutUser} />
    ];
  }

  renderContent() {
    const { session, user, status } = this.props;
    const { aboutShown } = this.state;

    if (session.error) {
      let loginMessage;

      if (!session.loggedIn) {
        loginMessage = (
          <React.Fragment>
            Please <a href="/login">login</a> to continue.
          </React.Fragment>
        );
      }

      return (
        <EmptyState className="full-page-blank-slate">
          <Alert type="error">
            <span>
              Login error: {session.errorMessage.replace(/\.$/, '')}. {loginMessage}
            </span>
          </Alert>
        </EmptyState>
      );
    }

    if (session.pending || !session.fulfilled || (!session.loggedIn && !session.wasLoggedIn)) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Logging in...</div>
          </Modal.Body>
        </Modal>
      );
    }

    return (
      <React.Fragment>
        <Content />
        <ToastNotificationsList key="toastList" />
        <ConfirmationModal key="confirmationModal" />
        <About user={user} status={status} shown={aboutShown} onClose={this.closeAbout} />
        <AddSourceWizard />
        <CreateCredentialDialog />
      </React.Fragment>
    );
  }

  render() {
    const { user, session, logoutUser } = this.props;

    if (!session.loggedIn && session.wasLoggedIn) {
      window.location = '/logout';
    }

    const titleImg = helpers.RH_BRAND ? rhProductTitle : productTitle;

    if (!session.loggedIn) {
      return (
        <div className="layout-pf layout-pf-fixed">
          <nav className="navbar navbar-pf-vertical">
            <div className="navbar-header">
              <span className="navbar-brand">
                <img className="navbar-brand-name" src={titleImg} alt="" />
              </span>
            </div>
          </nav>
          <div>{this.renderContent()}</div>
        </div>
      );
    }

    return (
      <div className="layout-pf layout-pf-fixed">
        <VerticalNav persistentSecondary={false}>
          <VerticalNav.Masthead>
            <VerticalNav.Brand titleImg={titleImg} />
            <MastheadOptions user={user} showAboutModal={this.showAbout} logoutUser={logoutUser} />
          </VerticalNav.Masthead>
          {this.renderMenuItems()}
          {this.renderMenuActions()}
        </VerticalNav>
        <div className="container-pf-nav-pf-vertical">{this.renderContent()}</div>
      </div>
    );
  }
}

App.propTypes = {
  authorizeUser: PropTypes.func,
  getUser: PropTypes.func,
  getStatus: PropTypes.func,
  logoutUser: PropTypes.func,
  session: PropTypes.object,
  user: PropTypes.object,
  status: PropTypes.object,
  location: PropTypes.object,
  history: PropTypes.shape({
    push: PropTypes.func.isRequired
  }).isRequired
};

const mapDispatchToProps = dispatch => ({
  authorizeUser: () => dispatch(authorizeUser()),
  getUser: () => dispatch(getUser()),
  logoutUser: () => dispatch(logoutUser()),
  getStatus: () => dispatch(getStatus())
});

const mapStateToProps = state => ({
  session: state.user.session,
  user: state.user.user,
  status: state.status.currentStatus
});

export default withRouter(
  connect(
    mapStateToProps,
    mapDispatchToProps
  )(App)
);
