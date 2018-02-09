import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Dropdown, Icon, MenuItem } from 'patternfly-react';

import Store from '../../redux/store';
import { getUser, logoutUser } from '../../redux/actions/userActions';
import { aboutTypes } from '../../redux/constants';
import helpers from '../../common/helpers';

class MastheadOptions extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['logout']);
  }

  componentDidMount() {
    this.props.getUser();
  }

  showAboutModal() {
    Store.dispatch({ type: aboutTypes.ABOUT_DIALOG_OPEN });
  }

  logout() {
    this.props.logoutUser();
  }

  render() {
    const { user } = this.props;
    return (
      <nav className="collapse navbar-collapse">
        <ul className="navbar-iconic nav navbar-nav navbar-right">
          <Dropdown componentClass="li" id="help">
            <Dropdown.Toggle useAnchor className="nav-item-iconic">
              <Icon type="pf" name="help" />
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <MenuItem>Help</MenuItem>
              <MenuItem onClick={this.showAboutModal}>About</MenuItem>
            </Dropdown.Menu>
          </Dropdown>
          <Dropdown componentClass="li" id="user">
            <Dropdown.Toggle useAnchor className="nav-item-iconic">
              <Icon type="pf" name="user" />{' '}
              {user.currentUser && user.currentUser.userName}
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <MenuItem onClick={this.logout}>Logout</MenuItem>
            </Dropdown.Menu>
          </Dropdown>
        </ul>
      </nav>
    );
  }
}

MastheadOptions.propTypes = {
  getUser: PropTypes.func,
  logoutUser: PropTypes.func,
  user: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getUser: () => dispatch(getUser()),
  logoutUser: () => dispatch(logoutUser())
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.sources.view, state.sources.persist, {
    user: state.user.user
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(MastheadOptions);
