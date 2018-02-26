import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Dropdown, Icon, MenuItem } from 'patternfly-react';
import { getUser } from '../../redux/actions/userActions';

class MastheadOptions extends React.Component {
  componentDidMount() {
    this.props.getUser();
  }

  render() {
    const { user, logoutUser, showAboutModal } = this.props;

    return (
      <nav className="collapse navbar-collapse">
        <ul className="navbar-iconic nav navbar-nav navbar-right">
          <Dropdown componentClass="li" id="help">
            <Dropdown.Toggle useAnchor className="nav-item-iconic">
              <Icon type="pf" name="help" />
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <MenuItem onClick={showAboutModal}>About</MenuItem>
            </Dropdown.Menu>
          </Dropdown>
          <Dropdown componentClass="li" id="user">
            <Dropdown.Toggle useAnchor className="nav-item-iconic">
              <Icon type="pf" name="user" /> {user.currentUser && user.currentUser.username}
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <MenuItem onClick={logoutUser}>Logout</MenuItem>
            </Dropdown.Menu>
          </Dropdown>
        </ul>
      </nav>
    );
  }
}

MastheadOptions.propTypes = {
  getUser: PropTypes.func,
  user: PropTypes.object,
  logoutUser: PropTypes.func,
  showAboutModal: PropTypes.func
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getUser: () => dispatch(getUser())
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.sources.view, state.sources.persist, {
    user: state.user.user
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(MastheadOptions);
