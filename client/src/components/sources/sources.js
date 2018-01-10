import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';
import { getSources } from '../../redux/actions/sourcesActions';

class Sources extends React.Component {

  componentDidMount() {
    this.props.getSources();
  }

  render() {
    const { error, loading, data } = this.props;
    return (
      <div>
        <h1>Sources</h1>
        loading {loading.toString()} <br/>
        error {error.toString()} <br/>
        <ul>
          {data.map((item) => (
            <li>
              {JSON.stringify(item)}
            </li>
          ))}
        </ul>
      </div>
    );
  }
}
Sources.propTypes = {
  getSources: PropTypes.func,
  error: PropTypes.bool,
  loading: PropTypes.bool,
  data: PropTypes.array
};

const mapStateToProps = state => ({
  error: state.sources.error,
  loading: state.sources.loading,
  data: state.sources.data
});

const mapDispatchToProps = (dispatch, ownProps) => ({
  getSources: () => dispatch(getSources())
});

export default connect(mapStateToProps, mapDispatchToProps)(Sources);

