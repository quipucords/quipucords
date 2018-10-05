import React from 'react';
import PropTypes from 'prop-types';
import InfiniteScroll from 'react-infinite-scroller';
import { connect } from 'react-redux';
import { EmptyState, Grid } from 'patternfly-react';
import _ from 'lodash';
import helpers from '../../common/helpers';
import { getConnectionScanResults, getInspectionScanResults } from '../../redux/actions/scansActions';

class ScanHostList extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['loadMore']);

    this.state = {
      scanResults: [],
      scanResultsError: false,
      connectionScanResultsPending: false,
      inspectionScanResultsPending: false,
      moreResults: false,
      prevResults: []
    };

    this.loading = false;
  }

  componentDidMount() {
    this.refresh(this.props);
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (
      !_.isEqual(nextProps.lastRefresh, this.props.lastRefresh) ||
      nextProps.status !== this.props.status ||
      nextProps.useConnectionResults !== this.props.useConnectionResults ||
      nextProps.useInspectionResults !== this.props.useInspectionResults
    ) {
      this.refresh(nextProps);
    }
  }

  addResults(results) {
    const { scanResults } = this.state;
    const { useConnectionResults, useInspectionResults } = this.props;

    const newResults = _.get(results, 'value.data.results', []);
    const allResults = [...scanResults, ...newResults];

    if (useConnectionResults && useInspectionResults) {
      allResults.sort((item1, item2) => {
        if (helpers.isIpAddress(item1.name) && helpers.isIpAddress(item2.name)) {
          const value1 = helpers.ipAddressValue(item1.name);
          const value2 = helpers.ipAddressValue(item2.name);

          return value1 - value2;
        }

        return item1.name.localeCompare(item2.name);
      });
    }

    return allResults;
  }

  getInspectionResults(page, status) {
    const { scanId, sourceId, getInspectionScanResults, useConnectionResults, useInspectionResults } = this.props;
    const fetchAll = useConnectionResults && useInspectionResults;

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status
    };

    if (sourceId) {
      queryObject.source_id = sourceId;
    }

    getInspectionScanResults(scanId, queryObject)
      .then(results => {
        const morePages = fetchAll && _.get(results.value, 'data.next') !== null;

        this.setState({
          inspectionScanResultsPending: morePages,
          scanResults: this.addResults(results),
          prevResults: morePages || this.state.connectionScanResultsPending ? this.state.prevResults : []
        });
        this.loading = this.state.connectionScanResultsPending;

        if (morePages) {
          this.getInspectionResults(page + 1, status);
        }
      })
      .catch(error => {
        this.setState({
          inspectionScanResultsPending: false,
          scanResultsError: helpers.getErrorMessageFromResults(error)
        });
      });
  }

  getConnectionResults(page, status) {
    const { scanId, sourceId, getConnectionScanResults, useConnectionResults, useInspectionResults } = this.props;
    const usePaging = !useConnectionResults || !useInspectionResults;

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status
    };

    if (sourceId) {
      queryObject.source_id = sourceId;
    }

    getConnectionScanResults(scanId, queryObject)
      .then(results => {
        const allResults = this.addResults(results);
        const morePages = _.get(results.value, 'data.next') !== null;

        this.setState({
          moreResults: morePages,
          connectionScanResultsPending: morePages && !usePaging,
          scanResults: allResults,
          prevResults: morePages || this.state.inspectionScanResultsPending ? this.state.prevResults : []
        });
        this.loading = this.state.inspectionScanResultsPending;

        if (morePages && !usePaging) {
          this.getConnectionResults(page + 1, status);
        }
      })
      .catch(error => {
        this.setState({
          connectionScanResultsPending: false,
          scanResultsError: helpers.getErrorMessageFromResults(error)
        });
      });
  }

  refresh(useProps, page = 1) {
    const { useConnectionResults, useInspectionResults, status } = useProps;

    this.setState({
      scanResultsPending: true,
      connectionScanResultsPending: useConnectionResults,
      inspectionScanResultsPending: useInspectionResults,
      scanResults: page === 1 ? [] : this.state.scanResults,
      prevResults: this.state.scanResults,
      moreResults: false
    });
    this.loading = true;

    if (useConnectionResults) {
      this.getConnectionResults(page, status);
    }

    if (useInspectionResults) {
      this.getInspectionResults(page, status);
    }
  }

  loadMore(page) {
    if (this.loading) {
      return;
    }

    this.loading = true;
    this.refresh(this.props, page);
  }

  renderResults(results) {
    const { renderHostRow } = this.props;
    const { moreResults } = this.state;

    if (_.size(results) === 0) {
      return null;
    }

    const rowItems = results.map(host => (
      <Grid.Row key={`${host.name}-${host.source.id}`}>{renderHostRow(host)}</Grid.Row>
    ));

    return (
      <div className="host-results">
        <Grid fluid className="host-list">
          <InfiniteScroll
            pageStart={1}
            loadMore={this.loadMore}
            hasMore={moreResults}
            useWindow={false}
            loader={
              <div key="loader" className="loader">
                Loading...
              </div>
            }
          >
            {rowItems}
          </InfiniteScroll>
        </Grid>
      </div>
    );
  }

  render() {
    const { status, useConnectionResults, useInspectionResults } = this.props;
    const {
      scanResults,
      connectionScanResultsPending,
      inspectionScanResultsPending,
      scanResultsError,
      prevResults
    } = this.state;
    const usePaging = !useConnectionResults || !useInspectionResults;

    if ((!_.size(scanResults) || !usePaging) && (inspectionScanResultsPending || connectionScanResultsPending)) {
      return (
        <React.Fragment>
          <EmptyState>
            <EmptyState.Icon name="spinner spinner-xl" />
            <EmptyState.Title>Loading scan results...</EmptyState.Title>
          </EmptyState>
          <div className="hidden-results">{this.renderResults(prevResults)}</div>
        </React.Fragment>
      );
    }

    if (scanResultsError) {
      return (
        <EmptyState>
          <EmptyState.Icon name="error-circle-o" />
          <EmptyState.Title>Error retrieving scan results</EmptyState.Title>
          <EmptyState.Info>{scanResultsError}</EmptyState.Info>
        </EmptyState>
      );
    }

    if (_.size(scanResults) === 0) {
      return (
        <EmptyState>
          <EmptyState.Icon name="warning-triangle-o" />
          <EmptyState.Title>
            {`${helpers.scanStatusString(status)} systems were not available, please refresh.`}
          </EmptyState.Title>
        </EmptyState>
      );
    }

    return this.renderResults(scanResults);
  }
}

ScanHostList.propTypes = {
  scanId: PropTypes.number,
  sourceId: PropTypes.number,
  lastRefresh: PropTypes.number,
  status: PropTypes.string,
  renderHostRow: PropTypes.func,
  useConnectionResults: PropTypes.bool,
  useInspectionResults: PropTypes.bool,
  getConnectionScanResults: PropTypes.func,
  getInspectionScanResults: PropTypes.func
};

ScanHostList.defaultProps = {
  useConnectionResults: false,
  useInspectionResults: false
};

const mapDispatchToProps = dispatch => ({
  getConnectionScanResults: (id, query) => dispatch(getConnectionScanResults(id, query)),
  getInspectionScanResults: (id, query) => dispatch(getInspectionScanResults(id, query))
});

const mapStateToProps = () => ({});

const ConnectedScanHostList = connect(
  mapStateToProps,
  mapDispatchToProps
)(ScanHostList);

export { ConnectedScanHostList as default, ConnectedScanHostList, ScanHostList };
